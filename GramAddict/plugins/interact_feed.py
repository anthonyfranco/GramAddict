import logging
from functools import partial
from random import seed

from colorama import Style

from GramAddict.core.decorators import run_safely
from GramAddict.core.handle_sources import handle_posts
from GramAddict.core.interaction import interact_with_user
from GramAddict.core.plugin_loader import Plugin
from GramAddict.core.utils import init_on_things

from GramAddict.core.views import (
    TabBarView
)


logger = logging.getLogger(__name__)

# Script Initialization
seed()


class InteractOwnFeed(Plugin):
    """Handles the functionality of interacting with your own feed"""

    def __init__(self):
        super().__init__()
        self.description = "Handles the functionality of interacting with your own feed"
        self.arguments = [
            {
                "arg": "--feed",
                "nargs": None,
                "help": "interact with your own feed",
                "metavar": "5-10",
                "default": None,
                "operation": True,
            },
            {
                "arg": "--feed-click-following",
                "nargs": None,
                "help": "click on 'Following' before interacting with feed",
                "metavar": None,
                "default": False,
                "operation": False,
            },
        ]

    def run(self, device, configs, storage, sessions, profile_filter, plugin):
        class State:
            def __init__(self):
                pass

            is_job_completed = False

        self.device_id = configs.args.device
        self.sessions = sessions
        self.session_state = sessions[-1]
        self.args = configs.args
        self.current_mode = plugin

        (
            active_limits_reached,
            _,
            actions_limit_reached,
        ) = self.session_state.check_limit(limit_type=self.session_state.Limit.ALL)
        limit_reached = active_limits_reached or actions_limit_reached

        self.state = State()
        logger.info("Interact with your own feed", extra={"color": f"{Style.BRIGHT}"})

        # Click on 'Following' if the option is enabled
        if self.args.feed_click_following:
            self.click_following(device)


        # Init common things
        (
            on_interaction,
            stories_percentage,
            likes_percentage,
            follow_percentage,
            comment_percentage,
            pm_percentage,
            interact_percentage,
        ) = init_on_things("Own Feed", self.args, self.sessions, self.session_state)

        @run_safely(
            device=device,
            device_id=self.device_id,
            sessions=self.sessions,
            session_state=self.session_state,
            screen_record=self.args.screen_record,
            configs=configs,
        )
        def job():
            self.handle_feed(
                device,
                plugin,
                storage,
                profile_filter,
                on_interaction,
                stories_percentage,
                likes_percentage,
                follow_percentage,
                comment_percentage,
                pm_percentage,
                interact_percentage,
            )
            self.state.is_job_completed = True

        while not self.state.is_job_completed and not limit_reached:
            job()

        if limit_reached:
            logger.info("Ending session.")
            self.session_state.check_limit(
                limit_type=self.session_state.Limit.ALL, output=True
            )
            return
    def click_following(self, device):
        logger.info("Clicking on 'Following' before interacting with feed")
        
        # Navigate to profile
        TabBarView(device).navigateToProfile()

        # Click on the top left corner (Instagram logo area)
        top_left_corner = device.find(
            resourceId='com.instagram.android:id/action_bar_container',
            className='android.widget.FrameLayout'
        ).child(
            resourceId='com.instagram.android:id/title_logo_chevron_container',
            className='android.widget.LinearLayout'
        )

        if top_left_corner.exists():
            logger.info("Clicking on the top left corner")
            top_left_corner.click()
            device.sleep(2)
        else:
            logger.error("Couldn't find the top left corner element")
            return

        # Click on "Following"
        following_button = device.find(
            resourceId='com.instagram.android:id/context_menu_item',
            className='android.widget.Button',
            content_desc='Following'
        )

        if following_button.exists():
            logger.info("Clicking on 'Following'")
            following_button.click()
            device.sleep(2)
        else:
            logger.error("Couldn't find the 'Following' button")
            return

        logger.info("Successfully clicked on 'Following'")


    def handle_feed(
        self,
        device,
        current_job,
        storage,
        profile_filter,
        on_interaction,
        stories_percentage,
        likes_percentage,
        follow_percentage,
        comment_percentage,
        pm_percentage,
        interact_percentage,
    ):
        interaction = partial(
            interact_with_user,
            my_username=self.session_state.my_username,
            likes_count=self.args.likes_count,
            likes_percentage=likes_percentage,
            stories_percentage=stories_percentage,
            follow_percentage=follow_percentage,
            comment_percentage=comment_percentage,
            pm_percentage=pm_percentage,
            profile_filter=profile_filter,
            args=self.args,
            session_state=self.session_state,
            scraping_file=self.args.scrape_to_file,
            current_mode=self.current_mode,
        )

        handle_posts(
            self,
            device,
            self.session_state,
            "Own Feed",
            current_job,
            storage,
            profile_filter,
            on_interaction,
            interaction,
            None,
            interact_percentage,
            self.args.scrape_to_file,
        )
