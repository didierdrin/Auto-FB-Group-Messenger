import time
import re
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
import random

# Add at the beginning of your script
def random_delay(min_seconds=1, max_seconds=3):
    """Sleep for a random amount of time between min and max seconds"""
    delay = min_seconds + random.random() * (max_seconds - min_seconds)
    time.sleep(delay)

class FacebookGroupMessenger:
    def __init__(self, email, password, headless=False):
        """
        Initialize the Facebook Group Messenger with your login credentials
        
        Args:
            email: Your Facebook email
            password: Your Facebook password
            headless: Whether to run the browser in headless mode
        """
        self.email = email
        self.password = password
        
        # Set up Edge options
        self.edge_options = Options()
        if headless:
            self.edge_options.add_argument("--headless")
        self.edge_options.add_argument("--no-sandbox")
        self.edge_options.add_argument("--disable-dev-shm-usage")
        self.edge_options.add_argument("--disable-notifications")  # Disable notifications
        
        # Use WebDriverManager to handle driver installation
        try:
            print("Setting up Edge driver with WebDriverManager")
            service = Service(EdgeChromiumDriverManager().install())
            self.driver = webdriver.Edge(service=service, options=self.edge_options)
            self.wait = WebDriverWait(self.driver, 20)
        except Exception as e:
            print(f"Error initializing Edge driver: {str(e)}")
            raise
    
    def login(self):
        """Log in to Facebook using provided credentials"""
        try:
            print("Navigating to Facebook login page...")
            self.driver.get("https://www.facebook.com/")
            
            # Accept cookies if prompted
            try:
                cookie_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Allow') or contains(text(), 'Accept')]")))
                cookie_button.click()
                print("Accepted cookies")
            except:
                print("No cookie prompt found or already accepted")
                
            # Enter email
            email_field = self.wait.until(EC.presence_of_element_located((By.ID, "email")))
            email_field.clear()
            email_field.send_keys(self.email)
            
            # Enter password
            password_field = self.wait.until(EC.presence_of_element_located((By.ID, "pass")))
            password_field.clear()
            password_field.send_keys(self.password)
            
            # Click login button
            login_button = self.wait.until(EC.element_to_be_clickable((By.NAME, "login")))
            login_button.click()
            
            # Wait for login to complete
            time.sleep(5)
            print("Login successful")
            
        except Exception as e:
            print(f"Login failed: {str(e)}")
            raise
    
    def extract_group_name(self, group_url):
        """Extract the group name from the URL"""
        # Regular expression to match the group name after the last slash
        match = re.search(r'/groups/([^/]+)', group_url)
        if match:
            return match.group(1)
        return None
    

    # In your customize_message method, ensure clean formatting:
    def customize_message(self, group_name):
        greeting = "Hey! "
        body = f"""I shared a gig in the freelancers group earlier, and it's still open.
        
    If you're into video editing for YouTube Shorts, check it out.

    Here's the kind of content I'm looking to create:
    https://youtube.com/shorts/IBIVrAyDnb0?feature=share"""
        
        return greeting, body
    
    def _show_cursor_marker(self):
        """Inject JavaScript to create a visible cursor marker"""
        js = """
        if (!window.cursorMarker) {
            window.cursorMarker = document.createElement('div');
            window.cursorMarker.style.position = 'absolute';
            window.cursorMarker.style.width = '10px';
            window.cursorMarker.style.height = '10px';
            window.cursorMarker.style.background = 'red';
            window.cursorMarker.style.borderRadius = '50%';
            window.cursorMarker.style.zIndex = '999999';
            window.cursorMarker.style.pointerEvents = 'none';
            window.cursorMarker.style.transform = 'translate(-50%, -50%)';
            document.body.appendChild(window.cursorMarker);
        }
        """
        self.driver.execute_script(js)

    def _move_cursor_marker(self, x, y):
        """Move the visible cursor marker to specified coordinates"""
        js = f"""
        if (window.cursorMarker) {{
            window.cursorMarker.style.left = '{x}px';
            window.cursorMarker.style.top = '{y}px';
        }}
        """
        self.driver.execute_script(js)

    def navigate_to_new_members(self, group_url):
        """Navigate to the 'New to the group' section of the Facebook group"""
        try:
            print(f"Navigating to group: {group_url}")
            self.driver.get(group_url)
            time.sleep(3)
            
            # Click on "People" tab
            people_tab = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/members/') or contains(text(), 'People') or contains(text(), 'Members')]")))
            people_tab.click()
            print("Clicked on People/Members tab")
            time.sleep(3)
            
            # Look for "New to the group" section
            new_members_section = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'New to the group') or contains(text(), 'ago')]/../..")))
            new_members_section.click()
            print("Navigated to 'New to the group' section")
            time.sleep(3)
            
        except Exception as e:
            print(f"Error navigating to new members: {str(e)}")
            raise
    
    def find_message_button(self):
        """Finds the message button on a profile page"""
        for selector in [
            "//div[contains(text(), 'Message')]",
            "//span[contains(text(), 'Message')]//ancestor::div[@role='button']",
            "//div[@aria-label='Message']"
        ]:
            try:
                message_btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if message_btn:
                    return message_btn
            except:
                continue
        return None
    

    def _keep_input_focused(self, input_element):
        """Enhanced helper to maintain focus on input element"""
        try:
            # First try JavaScript focus
            self.driver.execute_script("arguments[0].focus();", input_element)
            # Then attempt a click for good measure
            ActionChains(self.driver).move_to_element(input_element).click().perform()
            # Verify focus
            is_focused = self.driver.execute_script(
                "return document.activeElement === arguments[0]", 
                input_element
            )
            return is_focused
        except Exception as e:
            print(f"Error maintaining focus: {str(e)}")
            return False

    def send_message(self, greeting, body_message):
        """Send the message with enhanced focus control and cursor tracking"""
        try:
            # Wait for message box to be present and clickable
            msg_input = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//div[@role='textbox' and @contenteditable='true']"))
            )
            
            # Clear any existing text and ensure initial focus
            msg_input.clear()
            self._keep_input_focused(msg_input)
            time.sleep(random.uniform(0.3, 0.8))
            
            # Create complete message for tracking cursor position
            complete_message = greeting + "\n" + body_message
            current_pos = 0
            
            # Insert new line with JavaScript
            self._keep_input_focused(msg_input)
            self.driver.execute_script("""
                var el = arguments[0];
                el.focus();
                var sel = window.getSelection();
                var range = document.createRange();
                range.selectNodeContents(el);
                range.collapse(false);
                sel.removeAllRanges();
                sel.addRange(range);
                document.execCommand('insertLineBreak', false, null);
            """, msg_input)
            time.sleep(random.uniform(0.5, 1.0))
            
            # Type body message with enhanced focus management
            for i, char in enumerate(complete_message):
                # Re-check focus every few characters
                if i % 5 == 0:
                    self._keep_input_focused(msg_input)
                
                # Use JavaScript to insert character at current position
                self.driver.execute_script("""
                    var el = arguments[0];
                    el.focus();
                    var sel = window.getSelection();
                    var range = document.createRange();
                    range.selectNodeContents(el);
                    range.collapse(false);
                    sel.removeAllRanges();
                    sel.addRange(range);
                    document.execCommand('insertText', false, arguments[1]);
                """, msg_input, char)
                
                # Vary delays based on position in message and character type
                if i < 10:
                    time.sleep(random.uniform(0.1, 0.25))
                elif char in '.!?':
                    time.sleep(random.uniform(0.2, 0.4))
                elif char in ',;:':
                    time.sleep(random.uniform(0.15, 0.25))
                elif char == ' ':
                    time.sleep(random.uniform(0.08, 0.15))
                elif random.random() < 0.05:
                    time.sleep(random.uniform(0.3, 0.6))
                else:
                    time.sleep(random.uniform(0.05, 0.12))
            
            # Final focus check before sending
            self._keep_input_focused(msg_input)
            
            # Wait before sending (human-like hesitation)
            hesitation = random.uniform(0.5, 2.0)
            time.sleep(hesitation)
            
            # Try to send using button first (more reliable)
            try:
                send_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, 
                    "//div[@aria-label='Press Enter to send' or @aria-label='Send']"))
                )
                time.sleep(random.uniform(0.2, 0.5))
                send_button.click()
            except:
                # Fallback to ENTER key
                time.sleep(random.uniform(0.1, 0.3))
                self._keep_input_focused(msg_input)  # Ensure focus before sending
                msg_input.send_keys(Keys.RETURN)
            
            # Wait for message to be delivered
            time.sleep(random.uniform(2, 4))
            
            # Check for delivery confirmation or error
            try:
                error_indicator = WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located((By.XPATH, 
                    "//div[contains(text(), 'couldn't send') or contains(text(), 'Couldn't send')]"))
                )
                print("Message marked as 'couldn't send'")
                return False
            except:
                try:
                    success_indicator = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.XPATH, 
                        "//span[contains(text(), 'Delivered') or contains(text(), 'Sent')]"))
                    )
                    print("Message delivered successfully")
                    return True
                except:
                    print("Could not confirm message status, assuming sent")
                    return True
                    
        except Exception as e:
            print(f"Error in send_message: {str(e)}")
            return False
    


    def send_messages_to_new_members(self, group_url, max_members=1000):
        """Send messages to new members of the group by targeting 'ago' text"""
        # Setup and initialization
        group_name = self.extract_group_name(group_url)
        if not group_name:
            print("Could not extract group name from URL")
            return

        greeting, body_message = self.customize_message(group_name.replace('_', ' ').title())

        self.navigate_to_new_members(group_url)
        time.sleep(3)

        members_messaged = 0
        members_skipped = 0

        try:
            print("Starting member processing...")

            # First locate the "New to the group" heading
            try:
                new_to_group_heading = self.wait.until(EC.presence_of_element_located(
                    (By.XPATH, "//span[contains(text(), 'New to the group')]")))
                print("Found 'New to the group' heading")
            except Exception as e:
                print(f"Couldn't find 'New to the group' heading: {str(e)}")
                return 0, 0

            # Process members in batches
            batch_count = 0
            max_batches = max_members // 10 + 1

            while members_messaged + members_skipped < max_members and batch_count < max_batches:
                batch_count += 1
                print(f"Processing batch #{batch_count}")

                # In your send_messages_to_new_members method, after processing each batch:
                if batch_count % 3 == 0:  # Every 3 batches
                    cool_down = random.randint(30, 60)
                    print(f"Taking a break for {cool_down} seconds to avoid rate limiting...")
                    time.sleep(cool_down)

                # Find all elements containing 'ago' text
                ago_elements = []
                try:
                    for xpath in [
                        "//span[contains(text(), 'ago')]/..",
                        "//span[contains(text(), 'ago')]/ancestor::a",
                        "//div[contains(text(), 'minutes ago') or contains(text(), 'hour ago') or contains(text(), 'hours ago')]/..",
                    ]:
                        elements = self.driver.find_elements(By.XPATH, xpath)
                        if elements:
                            print(f"Found {len(elements)} potential member elements with 'ago' text using: {xpath}")
                            ago_elements = elements
                            break
                
                except Exception as e:
                    print(f"Error finding 'ago' elements: {str(e)}")

                # If no 'ago' elements found, try finding member names
                if not ago_elements:
                    print("Could not find elements with 'ago' text. Trying to find member names...")
                    try:
                        member_elements = self.driver.find_elements(
                            By.XPATH,
                            "//div[contains(@role, 'text') and .//span[contains(text(), 'Joined')]]"
                        )
                        if member_elements:
                            print(f"Found {len(member_elements)} potential member elements by 'Joined' text")
                            ago_elements = member_elements
                    except Exception as e:
                        print(f"Error finding member elements: {str(e)}")

                # Process up to 10 members per batch
                members_processed_in_batch = 0

                for i, element in enumerate(ago_elements):
                    if members_messaged + members_skipped >= max_members:
                        break

                    if members_processed_in_batch >= 10:
                        break

                    try:
                        # Get member name for logging
                        try:
                            member_name = element.find_element(By.XPATH, "./preceding-sibling::div[1]").text
                            if not member_name or "Joined" in member_name:
                                member_name = f"Member #{members_messaged + members_skipped + 1}"
                        except:
                            member_name = f"Member #{members_messaged + members_skipped + 1}"

                        print(f"Attempting to click on {member_name}")

                        # Scroll element into view with some offset
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block: 'center'}); window.scrollBy(0, -100);", 
                            element
                        )
                        time.sleep(2)

                        # Try different click strategies
                        try:
                            self._show_cursor_marker()

                            # Find the parent container
                            parent_container = element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'x16ldp7u')]")
                            print("Found parent container with class x16ldp7u")
                            
                            # Within that container, find the member name element
                            name_link = parent_container.find_element(By.CSS_SELECTOR, "a")
                            
                            # Visualize the click location
                            location = name_link.location
                            size = name_link.size
                            center_x = location['x'] + size['width']//2
                            center_y = location['y'] + size['height']//2
                            
                            self._move_cursor_marker(center_x, center_y)
                            time.sleep(1)
                            
                            # JavaScript click for reliability
                            self.driver.execute_script("arguments[0].click();", name_link)
                            print("Clicked on member name link directly")

                        except Exception as e:
                            print(f"Direct click failed: {str(e)}")
                            try:
                                # Strategy 2: Click slightly above the "ago" text
                                actions = ActionChains(self.driver)
                                
                                # Show movement to element with offset
                                location = element.location
                                size = element.size
                                target_x = location['x'] + size['width']//2 - 180
                                target_y = location['y'] - 35  # 35px above
                                self._move_cursor_marker(target_x, target_y)
                                time.sleep(1)
                                
                                actions.move_to_element(element).move_by_offset(0, -25).click().perform()
                                print("Clicked with -35px offset")
                            except Exception as e:
                                print(f"Offset click failed: {str(e)}")
                                try:
                                    # Strategy 3: JavaScript click on parent
                                    parent = element.find_element(By.XPATH, "./..")
                                    
                                    # Show movement to parent element
                                    location = parent.location
                                    size = parent.size
                                    self._move_cursor_marker(location['x'] + size['width']//2, location['y'] + size['height']//2)
                                    time.sleep(1)
                                    
                                    self.driver.execute_script("arguments[0].click();", parent)
                                    print("Used JavaScript click")
                                except Exception as e:
                                    print(f"JavaScript click failed: {str(e)}")
                                    raise

                        time.sleep(3)
                        
                        # Check for message button on profile page
                        message_btn = None
                        message_button_found = False

                        for selector in [
                            "//div[contains(text(), 'Message')]",
                            "//span[contains(text(), 'Message')]//ancestor::div[@role='button']",
                            "//a[contains(@href, '/messages/') and contains(text(), 'Message')]",
                            "//div[@aria-label='Message']"
                        ]:
                            try:
                                message_btn = WebDriverWait(self.driver, 5).until(
                                    EC.element_to_be_clickable((By.XPATH, selector))
                                )
                                if message_btn:
                                    message_button_found = True
                                    break
                            except:
                                continue

                        if message_button_found:
                            # We've successfully navigated to a profile page
                            print(f"Successfully navigated to {member_name}'s profile")

                            # Click on the message button
                            message_btn.click()
                            time.sleep(2)


                            # Check previous messages to avoid duplicates
                            try:
                                time.sleep(2)  # Let messages load
                                messages = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'x1yc453h') and contains(text(), '')]")  # Adjust the class or tag as needed
                                message_found = False
                                for msg in messages:
                                    if "gig in the freelancers group" in msg.text.lower():
                                        print("Already messaged this member. Skipping...")
                                        members_skipped += 1
                                        # Close chat and skip
                                        try:
                                            close_btn = self.driver.find_element(By.XPATH, "//div[@aria-label='Close chat']")
                                            close_btn.click()
                                        except:
                                            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                                        self.driver.back()
                                        time.sleep(2)
                                        raise Exception("Duplicate message found")
                            except Exception as e:
                                if "Duplicate message found" not in str(e):
                                    print(f"Error checking previous messages: {e}")
                                continue

                            

                            # Send messages using the improved method
                            try:
                                self.send_message(greeting, body_message)
                                members_messaged += 1
                                print(f"Sent messages to {member_name}")
                            except Exception as e:
                                print(f"Failed to send messages: {str(e)}")
                                members_skipped += 1

                            # Close chat
                            try:
                                close_btn = self.driver.find_element(By.XPATH, "//div[@aria-label='Close chat']")
                                close_btn.click()
                            except:
                                ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()

                            time.sleep(1)

                            # Go back to the members list
                            self.driver.back()
                            time.sleep(2)
                            members_processed_in_batch += 1
                        else:
                            print(f"Click on {member_name} didn't lead to a profile page with message button")
                            self.driver.back()
                            time.sleep(2)
                            members_skipped += 1
                            members_processed_in_batch += 1

                    except Exception as e:
                        print(f"Error processing member: {str(e)}")
                        members_skipped += 1
                        members_processed_in_batch += 1

                        try:
                            self.driver.back()
                            time.sleep(2)
                        except:
                            self.navigate_to_new_members(group_url)
                            time.sleep(3)

                # After processing 10 members, scroll down to load more
                if members_messaged + members_skipped < max_members:
                    print("Scrolling to load more members...")
                    self.driver.execute_script("window.scrollBy(0, 500);")
                    time.sleep(5)

            print(f"Finished: Messaged {members_messaged}, skipped {members_skipped}")
            return members_messaged, members_skipped
        except Exception as e:
            print(f"Error in send_messages_to_new_members: {str(e)}")
            return members_messaged, members_skipped

    def close(self):
        """Close the browser"""
        if hasattr(self, 'driver'):
            # Remove cursor marker before quitting
            try:
                self.driver.execute_script("""
                    if (window.cursorMarker) {
                        window.cursorMarker.remove();
                    }
                """)
            except:
                pass
            self.driver.quit()
            print("Browser closed")


if __name__ == "__main__":
    # Replace with your Facebook credentials
    email = "4313738873"
    password = "nse146DIDI2023!"
    
    # Example group URL
    group_url = "https://web.facebook.com/groups/665324318310939" #"https://web.facebook.com/groups/ineedavideoeditor"

    # Initialize and run the messenger
    try:
        messenger = FacebookGroupMessenger(email, password, headless=False)
        messenger.login()
        messenger.send_messages_to_new_members(group_url, max_members=200)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        if 'messenger' in locals():
            messenger.close()



