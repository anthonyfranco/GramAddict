from GramAddict.core.device_facade import DeviceFacade
from GramAddict.core.views import TabBarView, load_config
from GramAddict.core.utils import random_sleep
import uiautomator2 as u2
import time

# Connect to the device
device = u2.connect()  # This will use the default device or emulator

# Create DeviceFacade instance
device_facade = DeviceFacade(device.serial, 'com.instagram.android')

# Set a default speed multiplier for random_sleep
class Args:
    speed_multiplier = 1
    app_id = 'com.instagram.android'
    args = None

args = Args()
args.args = args  # Set the args attribute to itself

# Load the configuration to initialize ResourceID
load_config(args)

def click_top_left_corner():
    # Click on the Instagram logo area
    device_facade.find(
        resourceId='com.instagram.android:id/action_bar_container',
        className='android.widget.FrameLayout'
    ).child(
        resourceId='com.instagram.android:id/title_logo_chevron_container',
        className='android.widget.LinearLayout'
    ).click()
    
    time.sleep(2)  # Wait for the menu to appear

def click_following():
    following_button = device_facade.find(
        resourceId='com.instagram.android:id/context_menu_item',
        className='android.widget.Button',
        description='Following'
    )
    if following_button.exists():
        following_button.click()
        print("Clicked on Following")
    else:
        print("Following button not found")
    
    time.sleep(2)  # Wait for the page to load

def main():
    # Ensure Instagram is open
    TabBarView(device_facade).navigateToHome()
    time.sleep(2)

    # Click on the top left corner
    click_top_left_corner()

    # Click on Following
    click_following()

if __name__ == "__main__":
    main()