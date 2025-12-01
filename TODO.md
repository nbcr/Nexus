## Add profile page

- Create a user profile page with avatar, username, editable info, profile picture update, recent activity/history, and privacy/account settings quick links.

## Add settings page [COMPLETED ✅]

- ✅ Create a settings page with a sidebar for categories: Privacy Policy, Terms of Service, History, Account, Appearance. Each category loads content in the main area. Touch-friendly, modern layout.
- ✅ Implemented with full header, functional sidebar navigation
- ✅ History section has three tabs (Seen, Clicked, Read)
- ✅ All buttons functional (Clear History, Logout, Dark Mode toggle)
- ✅ API integration for loading history
- ✅ Account section displays user info from backend

## Update navigation/menu [COMPLETED ✅]

- ✅ Hamburger menu: icon above text, spaced items, quick links to Feed, Settings
- ✅ Login/Register remain in header on desktop, move to menu on mobile
- ✅ Dark/Light toggle labeled and functional in menu
- ✅ Text size controls added to menu
- ✅ Fixed height menu items maintain position during text resize

## Move links to settings page [COMPLETED ✅]

- ✅ Move Privacy Policy, Terms, History to settings page
- ✅ Make all menu and sidebar items touch-friendly
- ✅ Settings page sidebar buttons functional and responsive
# Project Todo List

## Improve login page layout

- Review and redesign login page for better vertical alignment and mobile responsiveness.
- Test on multiple devices and browsers.
- Review with user for usability and satisfaction.

## Hide login page after login

- Prevent access to login page after user is logged in (back button, direct URL).
- Implement logic in frontend and backend as needed.
- Test for security and UX.
- Review with user for expected behavior.

## Create privacy policy

- Draft privacy policy covering data usage, cookies, tracking, ads.
- Review for legal compliance and completeness.
- Publish on site and link from footer/menu.
- Review with user for clarity.

## Create terms of service

- Draft terms of service for user conduct, content, liability.
- Review for legal compliance and completeness.
- Publish on site and link from footer/menu.
- Review with user for clarity.

## Fix day/night option on mobile [COMPLETED ✅]

- ✅ Dark mode toggle fully functional on mobile in hamburger menu
- ✅ Dark mode toggle also in desktop header (removed from mobile separately)
- ✅ Theme persists across page loads via localStorage
- ✅ Works on all pages (index, login, register, settings)

## Shorten header on scroll (mobile) [NOT NEEDED]

- Current sticky header works well, no complaints
- Can revisit if user requests

## Create hamburger menu [COMPLETED ✅]

- ✅ Responsive hamburger menu implemented for mobile/desktop
- ✅ Three-bar icon that animates to X on open (removed animation per user preference)
- ✅ Navigation links: Feed, Settings
- ✅ Auth buttons: Login/Register on mobile, in header on desktop
- ✅ Dark mode toggle
- ✅ Text size controls
- ✅ Menu doesn't close when clicking text size or dark mode buttons
- ✅ Fixed height items prevent layout shift
- ✅ Consolidated JavaScript in header.js (no duplication)

## Add admin spot in hamburger menu [PENDING]

- Admin link logic exists in index.html (checks localStorage for is_admin)
- Not yet integrated into hamburger menu
- Need to add admin link to base.html template

## Add category buttons to top [COMPLETED ✅]

- ✅ Category filter buttons implemented above feed
- ✅ Dynamically loaded from /api/v1/topics/
- ✅ Active state highlighting
- ✅ Filter feed by category on click
- ✅ Styled with hover effects and proper spacing

## Allow users to set font size [COMPLETED ✅]

- ✅ Font size controls in hamburger menu (➖ Text Size ➕)
- ✅ Adjusts all content text (12px to 24px range)
- ✅ Excludes: Site title, card titles, menu controls
- ✅ Includes: Category buttons, descriptions, tags, queries, menu items
- ✅ Persists in localStorage
- ✅ Menu items maintain fixed height during resize
- ✅ MutationObserver handles dynamically loaded content

## Font size popup on first visit [DECLINED]

- User prefers in-menu controls, not a popup
- Feature implemented as menu controls instead

## Fix X on pop-up card

- Review pop-up card close button (X) for visibility and functionality on all devices.
- Refactor HTML/CSS/JS as needed for accessibility and mobile support.
- Test on desktop and mobile browsers.
- Review with user for UX approval.

## Improve story pop-up window UX

- Design pop-up window logic to close on X or back button.
- Implement in frontend JS/CSS.
- Test for reliability and user experience.
- Review with user for satisfaction.

## Lighten pop-up window colors

- Adjust pop-up window colors to visually differentiate from site background.
- Test for clarity in both light and dark modes.
- Review with user for visual distinction.

## Apply dark mode to pop-up pages

- Ensure dark mode colors are applied to any page opened in a pop-up window.
- Test for consistency and completeness.
- Review with user for dark mode experience.

## Show end of feed reached [COMPLETED ✅]

- ✅ "You've reached the end of the feed!" message implemented
- ✅ Styled for both light and dark mode
- ✅ Appears after all feed items loaded
- ✅ Prevents further API calls when no more content

## Show new stories first but also on scroll [COMPLETED ✅]

- ✅ Feed shows newest stories at the top
- ✅ Infinite scroll loads older stories as user scrolls
- ✅ WebSocket feed notifier alerts users to new content
- ✅ Page refresh loads latest stories first

## Balance story categories

- Analyze feed category distribution (especially sports).
- Tune category weighting and source selection logic.
- Test feed diversity and representation.
- Review with user for balance and satisfaction.

## RSS feed search by category

- Design RSS feed search logic for each category.
- Implement backend and frontend for category-based feed selection.
- Test with various categories and sources.
- Review for accuracy and usability.

## Differentiate stories by title

- Analyze current story differentiation logic.
- Improve title analysis for uniqueness and relevance.
- Test for uniqueness and relevance in feed.
- Review with user for effectiveness.

## Handle duplicate stories

- Identify causes of duplicate stories in feed (scraper, DB, frontend).
- Plan deduplication logic and where it should be applied (backend, frontend, or both).
- Implement deduplication logic in backend and/or frontend.
- Test with various feeds and sources to ensure duplicates are removed.
- Review feed for uniqueness and accuracy.

## Add images to scraped stories [COMPLETED ✅]

- ✅ Scraper extracts images from stories (picture_url in source_metadata)
- ✅ YouTube-style image display (360px × 200px with rounded corners)
- ✅ Images centered with auto margins
- ✅ Fallback: image container hidden if no image available
- ✅ Dominant color extraction from images for hover effects
- ✅ crossorigin="anonymous" for CORS support

## Scrape story on card open, cache result [COMPLETED ✅]

- ✅ Story content scraped on-demand when "Read Full Article" clicked
- ✅ /api/v1/content/snippet/{content_id} endpoint for fetching
- ✅ Cached in database (content_text field)
- ✅ Rate limiting implemented (20 requests per minute)
- ✅ Shows "No preview available" if scraping fails
- ✅ Links to original source as fallback

## AI bullet facts for stories

- Research and select AI model/service for fact extraction.
- Integrate AI to extract bullet-point facts for each story.
- Design UI for fact display in modal/card.
- Test with various story types and sources.
- Review for accuracy and usefulness with user feedback.

## Sign up for multiple ad sites

- Research and register for multiple ad networks.
- Integrate with backend for ad management and reporting.
- Review ad diversity and compliance.

## Place ads on site

- Design ad placement strategy for site layout.
- Integrate ad code (Google, other networks) into frontend.
- Test for performance, layout, and UX.
- Review with user for ad experience.

## Add Google Analytics tracking

- Integrate Google Analytics for site tracking.
- Test for data collection and privacy compliance.
- Review analytics data for accuracy.

## Track ad views and CTR in DB

- Design tracking logic for ad views and click-through rates.
- Implement metrics storage in database.
- Test reporting and analytics.
- Review with user for ad performance.

## Setup Beaver for DB analysis

- Integrate Beaver tool for database inspection and analysis.
- Test for compatibility and usefulness.
- Review with user for DB insights.

## AI suggest DB columns for tracking

- Use AI to recommend additional DB columns for better tracking.
- Review and implement as needed.
- Test for effectiveness.

## AI suggest targeted story methods

- Use AI to suggest ways to show users more targeted stories based on category traits.
- Review and implement best approaches.
- Test for improved targeting.

## AI suggest user tracking improvements

- Use AI to suggest ways to track users and serve better content.
- Review and implement best practices.
- Test for improved personalization.

## AI suggest changes/upgrades

- Use AI to analyze site and suggest improvements/upgrades.
- Review suggestions and prioritize with user.

## Restore previous feed on back after refresh

- Design logic to reload previous feed items if user hits back after refreshing.
- Implement in frontend JS.
- Test for reliability and expected behavior.
- Review with user for satisfaction.

---

- Mark tasks as [in-progress] or [completed] as you work.
- Add new tasks as needed.
- I can read, update, and manage this list for you automatically.
