from GramAddict.core.plugin_loader import Plugin
from GramAddict.core.decorators import run_safely
from GramAddict.core.utils import init_on_things, get_value
from GramAddict.core.views import TabBarView, PostsViewList, LikeMode, SwipeTo
from GramAddict.core.device_facade import DeviceFacade, Direction
from GramAddict.core.resources import ResourceID

import logging
from colorama import Style
import time

logger = logging.getLogger(__name__)

class InteractFollowingFeed(Plugin):
    """Interacts with posts from the 'Following' feed"""

    def __init__(self):
        super().__init__()
        self.description = "Interacts with posts from the 'Following' feed"
        self.arguments = [
            {
                "arg": "--interact-following-feed",
                "nargs": "?",
                "help": "number of posts to interact with from the 'Following' feed (-1 for unlimited)",
                "metavar": "N",
                "default": None,
                "operation": True,
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
        self.ResourceID = ResourceID(self.args.app_id)
        self.current_mode = plugin

        self.state = State()
        logger.info("Interact with 'Following' feed", extra={"color": f"{Style.BRIGHT}"})

        @run_safely(
            device=device,
            device_id=self.device_id,
            sessions=self.sessions,
            session_state=self.session_state,
            screen_record=self.args.screen_record,
            configs=configs,
        )
        def job():
            self.interact_following_feed(device)
            self.state.is_job_completed = True

        while not self.state.is_job_completed:
            job()

    def interact_following_feed(self, device):
        device_facade = device  # Use the existing DeviceFacade instance
        tab_bar = TabBarView(device_facade)
        posts_view_list = PostsViewList(device_facade)

        if not tab_bar.navigateToHome():
            logger.error("Unable to navigate to Home tab.")
            return

        self.interact_with_stories(device_facade)
        self.click_following_button(device_facade)

        # Get the number of posts to interact with
        posts_count = get_value(self.args.interact_following_feed, None, -1)
        posts_interacted = 0

        while True:
            if posts_view_list._check_if_liked():
                logger.info("Encountered a liked post. Stopping interaction.")
                break

            posts_view_list._like_in_post_view(LikeMode.SINGLE_CLICK)
            self.session_state.totalLikes += 1
            posts_interacted += 1
            logger.info(f"Liked post {posts_interacted}. Total likes: {self.session_state.totalLikes}")

            if self.session_state.check_limit(limit_type=self.session_state.Limit.LIKES):
                logger.info("Reached like limit. Stopping interaction.")
                break

            if posts_count != -1 and posts_interacted >= posts_count:
                logger.info(f"Reached the specified number of posts ({posts_count}). Stopping interaction.")
                break

            posts_view_list.swipe_to_fit_posts(SwipeTo.NEXT_POST)
            time.sleep(2)  # Wait for the next post to load


    def interact_with_stories(self, device_facade):
        logger.info("Interacting with stories")
        
        # Click on the first story (not the user's own story)
        first_story = device_facade.find(
            resourceId='com.instagram.android:id/avatar_image_view',
            descriptionMatches=r".*'s story at column 1\. Unseen\..*"
        )
        if not first_story.exists():
            logger.info("No stories found")
            return
        
        first_story.click()
        time.sleep(2)  # Wait for the story to load

        while True:
            # Check if it's a sponsored story
            sponsored_text = device_facade.find(
                resourceId='com.instagram.android:id/reel_viewer_subtitle',
                text='Sponsored'
            )
            if sponsored_text.exists():
                logger.info("Skipping sponsored story")
            else:
                # Like the story if not liked in the last 20 hours
                if self.can_like_story():
                    like_button = device_facade.find(
                        resourceId='com.instagram.android:id/toolbar_like_button',
                        description='Like'
                    )
                    if like_button.exists():
                        like_button.click()
                        logger.info("Liked the story")
                        self.update_story_like_time()

            # Move to the next story
            device_facade.swipe(Direction.LEFT)
            time.sleep(1)

            # Check if we've reached the end of stories
            reel_viewer = device_facade.find(
                resourceId='com.instagram.android:id/reel_viewer_root'
            )
            if not reel_viewer.exists():
                logger.info("Reached the end of stories")
                break

        # Exit stories view
        device_facade.back()

    def can_like_story(self):
        # Implement logic to check if the story can be liked (not liked in the last 20 hours)
        # You'll need to store and check the last like time for each user
        return True  # Placeholder implementation

    def update_story_like_time(self):
        # Implement logic to update the last like time for the current user
        pass

    def click_following_button(self, device_facade):
        logger.info("Clicking on 'Following' button")
        
        top_left_corner = device_facade.find(
            resourceId='com.instagram.android:id/action_bar_container',
            className='android.widget.FrameLayout'
        ).child(
            resourceId='com.instagram.android:id/title_logo_chevron_container',
            className='android.widget.LinearLayout'
        )

        if top_left_corner.exists():
            logger.info("Clicking on the top left corner")
            top_left_corner.click()
            time.sleep(2)
        else:
            logger.error("Couldn't find the top left corner element")
            return

        following_button = device_facade.find(
            resourceId='com.instagram.android:id/context_menu_item',
            className='android.widget.Button',
            description='Following'
        )

        if following_button.exists():
            logger.info("Clicking on 'Following'")
            following_button.click()
            time.sleep(2)
        else:
            logger.error("Couldn't find the 'Following' button")
            return

        logger.info("Successfully clicked on 'Following'")