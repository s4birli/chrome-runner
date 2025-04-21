import subprocess
import time
import os
import pyautogui
import random

# Add safety pause between pyautogui operations
pyautogui.PAUSE = 1.0
# Enable fail-safe (move mouse to corner to stop)
pyautogui.FAILSAFE = True

def open_chrome():
    # First, try to close any existing Chrome windows
    if os.name == 'posix':  # Linux/Unix
        subprocess.run(['pkill', 'chrome'])
        time.sleep(2)  # Wait for Chrome to close
    
    # Open Chrome with a new window
    subprocess.Popen(['google-chrome-stable'])
    time.sleep(5)  # Wait for Chrome to open
    
    # Navigate to YouTube in the current tab
    pyautogui.hotkey('ctrl', 'l')  # Focus address bar
    time.sleep(0.5)
    pyautogui.write('https://youtube.com')
    time.sleep(0.5)
    pyautogui.press('enter')
    time.sleep(5)  # Wait for YouTube to load

def interact_with_youtube():
    try:
        # Scroll down using space key multiple times
        for _ in range(random.randint(3, 5)):
            pyautogui.press('space')
            time.sleep(1)  # Wait between scrolls
        
        time.sleep(3)  # Wait for videos to load
        
        # Move mouse to a random position in the middle area of screen where videos usually are
        screen_width, screen_height = pyautogui.size()
        x = random.randint(int(screen_width * 0.3), int(screen_width * 0.7))
        y = random.randint(int(screen_height * 0.4), int(screen_height * 0.6))
        
        # Move and click
        pyautogui.moveTo(x, y)
        time.sleep(1)  # Pause before clicking
        pyautogui.click()
        
        # Wait for 10-15 seconds
        watch_time = random.randint(20, 30)
        time.sleep(watch_time)
        
        # Close Chrome window
        if os.name == 'posix':  # Linux/Unix
            subprocess.run(['pkill', 'chrome'])
    except Exception as e:
        print(f"Error during YouTube interaction: {e}")
        # Try to close Chrome even if there was an error
        if os.name == 'posix':
            subprocess.run(['pkill', 'chrome'])

def main():
    print("Starting Chrome runner...")
    while True:
        try:
            open_chrome()
            interact_with_youtube()
            print("Completed one cycle. Waiting for next...")
            # Wait for 60 seconds before next cycle
            time.sleep(60)
        except KeyboardInterrupt:
            print("\nStopping Chrome runner...")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(60*60*3)  # Wait a minute before retrying

if __name__ == "__main__":
    main() 