# User Guide (under construction 🚧)

## Installation & Setup

### Prerequisites

### Installation

### Directories and Special Files

## Step 1: Context Selection

The first step is to select the context that the AI will use as a basis for generating content. You have three options:

* **Select Saved Context:** Choose from a list of previously saved contexts. You can filter the list by name or tags.
* **Upload New Context:** Upload one or more text files (.txt, .docx, .doc, or .pdf) to create a new context. You can
  give the context a name and add tags for easier retrieval later.
* **Skip Context:** If you don't need to provide any context, you can skip this step.
  Once you have selected or uploaded a context, the UI will display the number of tokens and the approximate size in MB.
  This information helps you estimate the cost of using the AI and ensure that the context fits within the model's
  limits.

## Step 2: Instructions and Prompts

Next, you will provide instructions and prompts to guide the AI's content generation.

### Enter System Instructions

System instructions provide high-level guidance to the AI about the overall task and the desired style and tone of the
output. You can select multiple system instructions from a pre-defined list, which you can filter by keywords.

### Enter User Prompts

User prompts are more specific instructions that tell the AI what to generate. You can select multiple user prompts from
a pre-defined list, which you can also filter by keywords. Additionally, you can enter a custom user prompt.

You can choose whether the custom user prompt should override the selected user prompts or be added at the end of them.

## Step 3: Output Settings

The final step is to configure the output settings.

### Set Output Requirements

* **Create This Type of Codex Object:** Choose whether to create a "Single Part of a Book (Part)" or a "Full Codex (
  Codex)".
* **Maximum output size in tokens:** Set the maximum number of tokens that the AI is allowed to generate (only for "
  Single Part of a Book").
* **Ensure Minimum Output:** Check this box to ensure that the AI generates at least a minimum number of tokens (only
  for "Single Part of a Book").
* **Minimum required output tokens:** Set the minimum number of tokens that the AI must generate (only for "Single Part
  of a Book").

### Set Output Destinations

* **Output directory:** Specify the directory where the generated content will be saved.
* **Output filename base:** Enter the base filename for the output file.
* **Log level:** Select the desired logging level for the process.
* **Plan Name:** Give your plan a descriptive name.

Once you have configured the output settings, click "Accept Output Settings" to add the plan to your multiplan. You can
then create additional plans or run the entire multiplan to generate content.

## Managing Multiple Plans

## Loading Saved Build Plans

## Userspaces
