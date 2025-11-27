## Add profile page

- Create a user profile page with avatar, username, editable info, profile picture update, recent activity/history, and privacy/account settings quick links.

## Add settings page

- Create a settings page with a sidebar for categories: Privacy Policy, Terms of Service, History, Account, Appearance. Each category loads content in the main area. Touch-friendly, modern layout.

## Update navigation/menu

- Hamburger menu: icon above text, spaced items, quick links to Feed, Settings, Profile, Admin.
- Login/Register remain in header.
- Dark/Light toggle labeled as such.

## Move links to settings page

- Move Privacy Policy, Terms, History to settings page.
- Make all menu and sidebar items touch-friendly.
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

## Fix day/night option on mobile

- Audit header/menu for mobile compatibility.
- Refactor day/night (dark mode) toggle for mobile visibility and usability.
- Test on various mobile devices and browsers.
- Review with user for mobile UX.

## Header hides on mobile scroll

- Design header auto-hide logic for mobile scroll.
- Implement in frontend JS/CSS.
- Test for smoothness and usability on mobile devices.
- Review with user for UX and feedback.

## Shorten header on scroll (mobile)

- Design header shrink/shorten effect for mobile scroll.
- Implement in frontend JS/CSS.
- Test for smoothness and visibility.
- Review with user for UX.

## Create hamburger menu

- Design and implement responsive hamburger menu for mobile/desktop.
- Add navigation links and controls.
- Test for usability and accessibility.
- Review with user for navigation experience.

## Add admin spot in hamburger menu

- Design admin link/section for hamburger menu for privileged users.
- Implement access control and visibility logic.
- Test for correct access and visibility.
- Review with admin users for usability.

## Add category buttons to top

- Design category selection buttons for top of window.
- Implement in frontend layout.
- Test for layout and responsiveness.
- Review with user for accessibility.

## Allow users to set font size

- Design font size setting UI for user preferences.
- Implement font size adjustment control in frontend.
- Persist setting per user/session (cookie/localStorage or DB).
- Test font scaling across site for accessibility.
- Review accessibility and user feedback.

## Font size popup on first visit

- Design font size selection popup for first-time users (per IP/session).
- Implement popup logic and persistence (cookie/localStorage).
- Test popup appearance and logic.
- Review UX for non-intrusiveness and clarity.

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

## Show end of feed reached

- Design UI indicator for end of feed (infinite scroll).
- Implement indicator in frontend code.
- Style message for both light and dark mode.
- Test with long feeds and edge cases.
- Review UX for clarity and user feedback.

## Show new stories first

- Audit feed sorting logic.
- Update backend/frontend to show newest stories at the top.
- Test with multiple sources and refreshes.
- Review for expected behavior and user feedback.

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

## Add images to scraped stories

- Audit scraper for image extraction capability.
- Enhance scraper to extract and display images.
- Test with multiple sources and formats.
- Review image quality and placement in UI.

## Scrape story on card open, cache result

- Refactor scraping logic to fetch story content only when card is opened.
- Implement caching of scraped content in DB for future use.
- Test for performance and reliability.
- Review with user for speed and accuracy.

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
