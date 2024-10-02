import argparse
import os
import re
import uuid

from google.api_core.client_options import ClientOptions
from google.cloud import documentai, storage


def batch_process_documents(
        project_id: str,
        location: str,
        processor_id: str,
        gcs_input_uri: str,
        input_mime_type: str,
        gcs_output_bucket: str,
        gcs_output_uri_prefix: str,
        output_dir: str,
        thisdoc_dir: str,
        timeout: int = 300,

):
    # You must set the api_endpoint if you use a location other than 'us', e.g.:
    opts = ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")

    client = documentai.DocumentProcessorServiceClient(client_options=opts)

    gcs_document = documentai.GcsDocument(
        gcs_uri=gcs_input_uri, mime_type=input_mime_type
    )

    # Load GCS Input URI into a List of document files
    gcs_documents = documentai.GcsDocuments(documents=[gcs_document])
    input_config = documentai.BatchDocumentsInputConfig(gcs_documents=gcs_documents)
    print('gcs_documents: {}'.format(gcs_documents))
    print('input_config: {}'.format(input_config))

    # NOTE: Alternatively, specify a GCS URI Prefix to process an entire directory
    #
    # gcs_input_uri = "gs://bucket/directory/"
    # gcs_prefix = documentai.GcsPrefix(gcs_uri_prefix=gcs_input_uri)
    # input_config = documentai.BatchDocumentsInputConfig(gcs_prefix=gcs_prefix)
    #

    # Cloud Storage URI for the Output Directory
    destination_uri = f"{gcs_output_bucket}/{gcs_output_uri_prefix}/"
    print(destination_uri)
    gcs_output_config = documentai.DocumentOutputConfig.GcsOutputConfig(
        gcs_uri=destination_uri
    )

    # Where to write results
    output_config = documentai.DocumentOutputConfig(gcs_output_config=gcs_output_config)

    # The full resource name of the processor, e.g.:
    # projects/project_id/locations/location/processor/processor_id
    # You must create new processors in the Cloud Console first
    name = client.processor_path(project_id, location, processor_id)

    # NOTE: Alternatively, specify the processor_version to specify a particular version of the processor to use
    # projects/{project_id}/locations/{location}/processors/{processor_id}/processorVersions/{processorVersion}
    #
    # name = client.processor_version_path(
    #     project_id, location, processor_id, processor_version
    # )
    #

    request = documentai.BatchProcessRequest(
        name=name,
        input_documents=input_config,
        document_output_config=output_config,
    )

    # BatchProcess returns a Long Running Operation (LRO)
    operation = client.batch_process_documents(request)

    # Continually polls the operation until it is complete.
    # This could take some time for larger files
    # Format: projects/PROJECT_NUMBER/locations/LOCATION/operations/OPERATION_ID
    print(f"Waiting for operation {operation.operation.name} to complete...")
    operation.result(timeout=timeout)

    # NOTE: Can also use callbacks for asynchronous processing
    #
    # def my_callback(future):
    #   result = future.result()
    #
    # operation.add_done_callback(my_callback)

    # Once the operation is complete,
    # get output document information from operation metadata
    metadata = documentai.BatchProcessMetadata(operation.metadata)

    if metadata.state != documentai.BatchProcessMetadata.State.SUCCEEDED:
        raise ValueError(f"Batch Process Failed: {metadata.state_message}")

    storage_client = storage.Client()

    print("Output files:")
    # One process per Input Document
    for process in metadata.individual_process_statuses:
        # output_gcs_destination format: gs://BUCKET/PREFIX/OPERATION_NUMBER/INPUT_FILE_NUMBER/
        # The Cloud Storage API requires the bucket name and URI prefix separately
        matches = re.match(r"gs://(.*?)/(.*)", process.output_gcs_destination)
        if not matches:
            print(
                "Could not parse output GCS destination:",
                process.output_gcs_destination,
            )
            continue

        output_bucket, output_prefix = matches.groups()

        # Get List of Document Objects from the Output Bucket
        output_blobs = storage_client.list_blobs(output_bucket, prefix=output_prefix)

        # Document AI may output multiple JSON files per source file
        for blob in output_blobs:
            # Document AI should only output JSON files to GCS
            if ".json" not in blob.name:
                print(
                    f"Skipping non-supported file: {blob.name} - Mimetype: {blob.content_type}"
                )
                continue

            # Download JSON File as bytes object and convert to Document Object
            print(f"Fetching {blob.name}")
            document = documentai.Document.from_json(
                blob.download_as_bytes(), ignore_unknown_fields=True
            )

            # For a full list of Document object attributes, please reference this page:
            # https://cloud.google.com/python/docs/reference/documentai/latest/google.cloud.documentai_v1.types.Document

            # Read the text recognition output from the processor
            # print("The bulk processeddocument contains the following text:")
            # print(document.text)

            # write the text to a local file
            target_file_path = output_dir + '/' + thisdoc_dir + '/' + blob.name.split('/')[-1]
            with open(target_file_path, 'w') as f:
                try:
                    f.write(document.text)
                    print('wrote to file: {}'.format(target_file_path))
                except Exception as e:
                    print('error writing text to file: {}'.format(e))

    return "Success"


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()

    argparser.add_argument(
        "--project_id", help="Your Google Cloud Project ID", default="531543480216"
    )
    argparser.add_argument(
        "--location", help="Your Google Cloud Project Location", default="us"
    )
    argparser.add_argument(
        "--processor_id", help="Your Document AI Processor ID", default="90e78beaca7a0ae6"
    )
    argparser.add_argument(
        "--gcs_input_uri", help="Your Cloud Storage Input URI",
        default="gs://test-lorem/lorem_with_roman_through_piii.pdf"
    )
    argparser.add_argument(
        "--input_mime_type", help="Your Cloud Storage Input MIME Type", default="application/pdf"
    )
    argparser.add_argument(
        "--gcs_output_bucket", help="Your Cloud Storage Output Bucket", default="gs://test-output-nimble"
    )
    argparser.add_argument(
        "--gcs_output_uri_prefix", help="Your Cloud Storage Output URI Prefix", default="output"
    )
    argparser.add_argument("--output_dir", help="Your Local Output Directory", default="output")
    argparser.add_argument("--thisdoc_dir", help="Your Local Thisdoc Directory", default='loremtest')
    args = argparser.parse_args()
    if args.thisdoc_dir == "thisdoc":
        # give thisdoc a random short name
        thisdoc_dir = str(uuid.uuid4())[:8]
    # make sure thisdoc_dir exists
    if not os.path.exists(args.output_dir + '/' + args.thisdoc_dir):
        os.makedirs(args.output_dir + '/' + args.thisdoc_dir)

    print(args)
    batch_process_documents(
        project_id=args.project_id,
        location=args.location,
        processor_id=args.processor_id,
        gcs_input_uri=args.gcs_input_uri,
        input_mime_type=args.input_mime_type,
        gcs_output_bucket=args.gcs_output_bucket,
        gcs_output_uri_prefix=args.gcs_output_uri_prefix,
        output_dir=args.output_dir,
        thisdoc_dir=args.thisdoc_dir,
    )
