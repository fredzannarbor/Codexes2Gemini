import streamlit as st
import random
import math
from PIL import Image, ImageDraw, ImageFont
from matplotlib import font_manager as fm

class Submarine:
    def __init__(self, name, fuel, food, crew_morale):
        self.name = name
        self.fuel = fuel  # barrels diesel
        self.food = food  # days
        self.crew_morale = crew_morale  # 0-100
        self.position = "Pearl Harbor"
        self.fuel_error_discovered = False
        self.total_distance = 0
        self.days_passed = 0

    def steam(self, direction, distance):
        self.total_distance += distance
        days_spent = distance // 100  # Assume 100 miles per day
        self.days_passed += days_spent
        if not self.fuel_error_discovered and self.total_distance > 50 and random.random() < 1 / 5:
            errormsg = f"Oh no! Due to a clerical mistake at the pier, your fuel tanks are empty. {self.name} is dead in the water."
            self.fuel = 0
            self.fuel_error_discovered = True
            st.error(errormsg)
            st.toast(errormsg)

        if self.fuel >= distance:
            self.fuel -= distance
            if direction in ['north', 'south', 'east', 'west', 'hilo']:
                self.position = direction.capitalize()
            else:
                self.position = "At Sea"

            self.food -= days_spent
            self.crew_morale -= random.randint(1, 3)
            if self.crew_morale < 0:
                self.crew_morale = 0


    def resupply(self, fuel, food):
        self.fuel += fuel
        self.food += food
        self.days_passed += 1
        st.success(f"{self.name} has been resupplied with {fuel} fuel and {food} food.")
        self.crew_morale += random.randint(5, 10)
        if self.crew_morale > 100:
            self.crew_morale = 100
        st.info(f"Crew morale: {self.crew_morale}.")

    def check_status(self):
        st.write(f"\n{self.name} Status:\n")
        st.write(f"Fuel: {self.fuel} miles remaining at cruise")
        st.write(f"Food: {self.food} days")
        st.write(f"Crew Morale: {self.crew_morale}")
        st.write(f"Position: {self.position}")
        st.write(f"Total Distance Traveled: {self.total_distance}")
        st.write(f"Days Passed: {self.days_passed}")

    def search(self, area_size):
        search_time = area_size // 10  # 10 square miles per hour
        days_spent = search_time // 24
        self.days_passed += days_spent
        self.fuel -= search_time * 5  # 5 fuel units per hour
        self.food -= days_spent
        self.crew_morale -= random.randint(1, 3)

        success_chance = min(area_size / 1000, 0.1)  # Max 10% chance of success
        if random.random() < success_chance:
            st.success(f"After searching for {search_time} hours, you've found signs of the Conestoga!")
            return True
        else:
            st.info(f"After searching for {search_time} hours, you haven't found any signs of the Conestoga.")
            return False

    @staticmethod
    def show_intro():
        st.title("Submarine Adventure: R-14")
        st.write('''
        This is the story of the interwar US Navy submarine R-14 that departed Pearl Harbor in May 1921 to search for the Navy oiler _Conestoga_, missing at sea. A few days later, encountered highly adverse circumstances that threatened loss of mission, boat, and crew. Your task is to find _Conestoga_, which left San Francisco more than a week ago.
        ''')
        st.sidebar.markdown(
            "[Buy the book on Amazon](https://amzn.to/3W65VWf) or via Nimble Books")

    @staticmethod
    def show_game_play():
        st.write('''
        Here are the rules:
        1. You can move, resupply, check status, exercise seamanship, or quit.
        2. Steaming consumes diesel fuel.
        3. Each day at sea consumes food.
        4. Crew morale varies depending on how you handle your efforts to find Conestoga.
        5. Resupply is possible at Pearl Harbor and Hilo.
        6. If things go wrong, you can exercise seamanship to overcome challenges.
        ''')

    @staticmethod
    @staticmethod
    def create_map(submarine):
        width, height = 400, 400
        image = Image.new('RGB', (width, height), color='lightblue')
        draw = ImageDraw.Draw(image)

        # Draw Oahu (Pearl Harbor)
        oahu_x, oahu_y = width // 2, height // 2 - 50
        oahu_size = 20
        draw.rectangle([oahu_x - oahu_size // 2, oahu_y - oahu_size // 2,
                        oahu_x + oahu_size // 2, oahu_y + oahu_size // 2], fill='green')
        draw.text((oahu_x - 30, oahu_y + 10), "Pearl Harbor", fill='black')

        # Draw Big Island (Hilo)
        hilo_x, hilo_y = width // 2 + 80, height // 2 + 80
        hilo_size = 30
        draw.rectangle([hilo_x - hilo_size // 2, hilo_y - hilo_size // 2,
                        hilo_x + hilo_size // 2, hilo_y + hilo_size // 2], fill='darkgreen')
        draw.text((hilo_x - 15, hilo_y + 15), "Hilo", fill='black')

        # Calculate submarine position
        if submarine.position == "Pearl Harbor":
            sub_x, sub_y = oahu_x, oahu_y
        elif submarine.position == "Hilo":
            sub_x, sub_y = hilo_x, hilo_y
        else:
            angle_rad = math.radians({'North': -90, 'South': 90, 'East': 0, 'West': 180}[submarine.position])
            distance = min(submarine.total_distance, 180)  # Cap at 180 for visibility
            sub_x = oahu_x + int(distance * math.cos(angle_rad))
            sub_y = oahu_y + int(distance * math.sin(angle_rad))

        # Draw submarine path
        draw.line((oahu_x, oahu_y, sub_x, sub_y), fill='red', width=2)

        # Draw submarine icon
        prop = fm.FontProperties(family='Calibri')
        font_file = fm.findfont(prop)
        font = ImageFont.truetype(font_file, 20)
        draw.text((sub_x - 10, sub_y - 10), "🚢", fill='black', font=font)

        return image

    def main(self):
        st.title("Submarine Adventure: R-14")

        if 'submarine' not in st.session_state:
            st.session_state.submarine = self
        else:
            # Update the current instance with the stored state
            self.__dict__.update(st.session_state.submarine.__dict__)

        sub = st.session_state.submarine

        # Display the map and days passed
        st.image(self.create_map(sub), caption=f"R-14's Position (Days Passed: {sub.days_passed})",
                 use_column_width=True)

        progress_messages = [
            "No new leads on the Conestoga's whereabouts.",
            "A faint radio signal was detected NNE, but quickly faded.",
            "Crew spotted some debris, but it wasn't from the Conestoga.",
            "Local fishermen reported seeing an unidentified vessel days ago about 100 mi S.",
            "Weather conditions are hampering the search efforts to the North.",
            "A passing ship reported seeing smoke on the horizon ESE yesterday.",
            "Naval radio intercepts of Japanese merchant traffic showing odd behavior to the west.",
            "An albatross with an unusual object in its claws was spotted. Could it be a clue?",
            "The crew's keen eyes caught a glimpse of something metallic in the water.",
            "A bottle with a message inside was found, but it wasn't from the Conestoga.",
            "Sonar picked up an unusual echo, but lost contact before we could investigate further.",
            "A drifting lifeboat was found, but it wasn't from the Conestoga. Search area expanded.",
            "Radio chatter from a distant station mentioned a ship in distress, but details were unclear.",
            "An oil slick was spotted on the water surface, origin unknown.",
            "A school of dolphins seemed to be trying to lead the submarine in a specific direction.",
            "The night watch reported seeing strange lights on the horizon, possibly a ship.",
            "An unexpected current has shifted our search pattern. Adjusting coordinates.",
            "A passing aircraft reported seeing a flare, but we couldn't confirm the location.",
            "Local island inhabitants shared stories of hearing distant explosions last week.",
            "Underwater volcanic activity is causing interference with our sonar equipment.",
            "A piece of driftwood with recent paint markings was recovered. Analysis underway.",
            "Unusual weather patterns are forcing us to recalculate likely drift scenarios.",
            "A flock of seabirds is circling persistently over one area. Worth investigating.",
            "Intercepted a garbled distress call, but couldn't pinpoint the source.",
            "Found traces of diesel fuel on the water's surface. Following the trail.",
            "Crew morale boosted by a potential sighting, but it turned out to be a false alarm.",
            "Naval headquarters radioed new information about the Conestoga's last known heading.",
            "A passing freighter reported seeing a adrift vessel matching Conestoga's description two days ago.",
            "Detected an unexpected magnetic anomaly. Could be wreckage on the seafloor.",
            "An old fisherman's tale about a 'ghost ship' has given us a new area to search."
        ]
        random.shuffle(progress_messages)

        # Create a stable info box for status
        status_box = st.empty()

        # Update status display
        def update_status_display():
            status_box.info(f"""
            {sub.name} Status:\n
            Fuel: {sub.fuel} miles left\n
            Food: {sub.food} days left\n
            Crew Morale: {sub.crew_morale}\n
            Position: {sub.position}\n
            Total Distance Traveled: {sub.total_distance}\n
            Days Passed: {sub.days_passed}\n
            Progress Report: {progress_messages[sub.days_passed]}\n
            """)

        # Initial status display
        update_status_display()

        # Use a form to control when updates occur
        with st.form("game_actions"):
            action = st.selectbox("What would you like to do?",
                                  ["Select an action", "Steam", "Search", "Resupply", "Check Status",
                                   "Exercise Seamanship",
                                   "Quit"])

            if action == "Steam":
                direction = st.selectbox("Which direction to steam?", ["North", "South", "East", "West", "Hilo"])
                distance = st.number_input("How many miles to steam?", min_value=1, value=100)

            elif action == "Search":
                area_size = st.number_input("How many square miles to search?", min_value=10, value=100, step=10)

            elif action == "Resupply":
                if sub.position in ["Pearl Harbor", "Hilo"]:
                    fuel_amount = st.number_input("How much fuel to resupply?", min_value=0, value=1000)
                    food_amount = st.number_input("How much food to resupply?", min_value=0, value=50)
                else:
                    st.error("You can only resupply at Pearl Harbor or Hilo.")

            elif action == "Exercise Seamanship":
                exercise = st.text_input("Enter your seamanship action:")

            submitted = st.form_submit_button("Execute Action")

        if submitted:
            if action == "Steam":
                sub.steam(direction.lower(), distance)
            elif action == "Search":
                search_result = sub.search(area_size)
                if search_result:
                    st.balloons()
            elif action == "Resupply":
                if sub.position in ["Pearl Harbor", "Hilo"]:
                    sub.resupply(fuel_amount, food_amount)
            elif action == "Check Status":
                pass  # Status is always displayed, no need for additional action
            elif action == "Exercise Seamanship":
                if "sail" in exercise.lower():
                    st.success("Great idea!")
                else:
                    st.error("Nope, that didn't work. Still stuck.")
                sub.days_passed += 1
            elif action == "Quit":
                st.write("Thanks for playing!")
                st.stop()

            # Update the status display after action
            #update_status_display()

        # Always update the session state with the current instance
        st.session_state.submarine = sub



if __name__ == "__main__":
    sub = Submarine(name="R-14", fuel=9000, food=30, crew_morale=100)
    sub.main()