# Google AdSense Terms of Service - Compliance Guide

**Publisher ID:** `ca-pub-1529513529221142`  
**Site:** Nexus (https://comdat.ca)  
**Country:** Canada  
**Last Updated:** December 1, 2025

---

## Official Terms & Policies

By using Google AdSense, you agree to:
1. **AdSense Terms of Service** (these terms)
2. **[AdSense Program Policies](https://support.google.com/adsense/answer/48182)**
3. **[Content Policies](https://support.google.com/adsense/answer/1348688)**
4. **[Webmaster Quality Guidelines](https://support.google.com/webmasters/answer/35769)**
5. **[Ad Implementation Policies](https://support.google.com/adsense/answer/1346295)**
6. **[EU User Consent Policy](https://www.google.com/about/company/user-consent-policy/)**
7. **[Google Branding Guidelines](https://about.google/brand-resource-center/)**

---

## Key Requirements for Nexus

### ✅ Content Requirements

#### What We MUST Do:
- **Original Content**: Provide unique value - aggregating news with personalized feeds ✅
- **High-Quality Content**: Well-written, properly formatted articles ✅
- **User Value**: Help users find trending news efficiently ✅
- **Regular Updates**: Keep content fresh (we have automated fetching) ✅
- **Clear Navigation**: Easy-to-use interface ✅

#### What We MUST NOT Do:
- ❌ **NO scraped content** without adding substantial value
- ❌ **NO copyright violations** (we link to sources, not republishing)
- ❌ **NO misleading content** or clickbait
- ❌ **NO adult, violent, or illegal content**
- ❌ **NO content encouraging dangerous activities**
- ❌ **NO hate speech or discrimination**

### ✅ Ad Placement Rules

#### Valid Placements:
1. **Between Feed Articles** - In-feed native ads (every 3-5 articles)
2. **Article Modal** - In-article ads within content
3. **Sidebar** - Display ads on settings/other pages
4. **Anchor Ads** - Sticky bottom mobile ads

#### PROHIBITED Placements:
- ❌ Ads on error pages (404, 500, etc.)
- ❌ Ads on "under construction" pages
- ❌ Ads on login/registration pages
- ❌ Ads that obstruct content
- ❌ Ads in pop-ups or pop-unders
- ❌ More than 3 ad units per page (standard limit)

### ✅ Click Behavior Requirements

#### What We MUST Do:
- **Natural Clicks Only**: Let users click ads naturally
- **Clear Distinction**: Ads must be clearly labeled as "Advertisements"
- **No Deceptive Placement**: Don't place ads to trick users into clicking

#### What We MUST NOT Do:
- ❌ **NO click encouragement** ("Click these ads to support us")
- ❌ **NO click manipulation** (misleading labels, fake buttons)
- ❌ **NO artificial traffic** (bots, paid clicks, incentivized clicks)
- ❌ **NO self-clicking** our own ads
- ❌ **NO asking others to click** ads

### ✅ Traffic Requirements

#### Valid Traffic Sources:
- ✅ Organic search (Google, Bing, etc.)
- ✅ Direct navigation
- ✅ Social media sharing
- ✅ Email newsletters (non-incentivized)
- ✅ Legitimate referrals

#### PROHIBITED Traffic Sources:
- ❌ Paid clicks or incentivized traffic
- ❌ Pop-ups/pop-unders
- ❌ Traffic exchanges
- ❌ Automated traffic (bots)
- ❌ Misleading implementations

---

## Technical Implementation Requirements

### ✅ Ad Code Requirements

1. **Use Unmodified Code**: Never alter AdSense code
2. **Proper Placement**: Place code in `<head>` or `<body>`
3. **One Account Per Site**: Use only our Publisher ID
4. **Responsive Design**: Ads must work on mobile and desktop
5. **Page Performance**: Ads shouldn't significantly slow page load

### ✅ User Experience Requirements

1. **Content First**: Primary content must be visible without scrolling past ads
2. **No Overlay Ads**: Ads can't cover content
3. **No Excessive Ads**: Maximum 3 ad units per page
4. **No Ads in Emails**: Can't place AdSense code in emails
5. **Loading Indicators**: Show when content is loading

---

## Privacy & Consent Requirements

### ✅ Privacy Policy (REQUIRED)

Our privacy policy MUST include:
- ✅ We use Google AdSense
- ✅ Google uses cookies for personalized ads
- ✅ Users can opt-out at [www.aboutads.info](https://www.aboutads.info)
- ✅ Link to [Google's Privacy Policy](https://policies.google.com/privacy)

### ✅ Cookie Consent (EU/Canada)

For EU and Canadian users, we MUST:
- ✅ Get consent before storing cookies
- ✅ Provide clear information about data collection
- ✅ Allow users to reject cookies
- ✅ Respect user choices

**✅ IMPLEMENTED**: We have Consent Manager on the site

---

## Content-Specific Guidelines for News Sites

### ✅ What Makes Nexus Compliant:

1. **News Aggregation with Value**:
   - ✅ We curate trending stories
   - ✅ We provide personalized feeds
   - ✅ We track user preferences
   - ✅ We link to original sources
   
2. **User Engagement**:
   - ✅ Users can filter by category
   - ✅ Dark mode for better reading
   - ✅ Reading history tracking
   - ✅ Article previews and summaries

3. **Original Features**:
   - ✅ AI-powered personalization
   - ✅ Google Trends integration
   - ✅ Custom feed algorithm
   - ✅ History and preferences

### ⚠️ **CRITICAL COMPLIANCE ISSUE - REQUIRES IMMEDIATE ATTENTION**:

1. **❌ CURRENT PROBLEM: Full Article Scraping**:
   - **WE ARE CURRENTLY SCRAPING AND DISPLAYING FULL ARTICLES**
   - This violates copyright and likely AdSense content policies
   - Risk: Account suspension or termination
   - Status: **HIGH RISK**
   
2. **✅ REQUIRED FIX - Choose One Solution**:

   **Option A: Excerpt Only (RECOMMENDED)**
   - Show only first 300-500 words
   - Add "Continue reading on [source]" button
   - Opens original site in new tab
   
   **Option B: RSS Feeds**
   - Use official RSS/API feeds (with publisher permission)
   - Only show what publishers provide in feeds
   - More compliant but limited content
   
   **Option C: Reader Mode with Permission**
   - Get explicit permission from major publishers
   - Document permissions
   - Still risky without formal agreements

3. **Immediate Actions Needed**:
   - [ ] **DO NOT activate AdSense until this is fixed**
   - [ ] Modify `article_scraper.py` to limit content
   - [ ] Update modal to show excerpts only
   - [ ] Add prominent "Read full article on source" button
   - [ ] Consider adding rel="nofollow" to external links (optional)

---

## Monetization Best Practices

### ✅ Ad Placement Strategy for Nexus:

1. **Feed Page** (`/`):
   - In-feed ads every 3-5 articles
   - Sidebar ad (desktop only)
   - Anchor ad (mobile)
   
2. **Article Modal**:
   - In-article ad after 2-3 paragraphs
   - Don't place ads before first heading
   
3. **Settings Page** (`/settings`):
   - Sidebar ad only
   - No ads in critical UI areas

### ✅ Recommended Ad Types:

1. **Display Ads**: Standard image/text ads
2. **Native Ads**: Match site design
3. **In-feed Ads**: Blend with article feed
4. **Responsive Ads**: Adapt to screen size
5. **Auto Ads**: Let Google optimize (optional)

---

## Monitoring & Compliance

### ✅ What We Must Monitor:

1. **Invalid Click Activity**:
   - Watch for unusual click patterns
   - Monitor Analytics for suspicious traffic
   
2. **Content Quality**:
   - Ensure scraped content adds value
   - Remove broken links promptly
   - Keep content appropriate
   
3. **User Experience**:
   - Page load speed
   - Ad placement doesn't obstruct content
   - Mobile responsiveness

### ✅ Policy Violation Prevention:

1. **Regular Audits**:
   - Review ad placements monthly
   - Check content for policy violations
   - Test on multiple devices
   
2. **Traffic Quality**:
   - Monitor Google Analytics
   - Watch for bot traffic
   - Ensure organic growth

---

## Account Health & Payments

### ✅ Payment Requirements:

1. **Verification**:
   - Verify AdSense account
   - Provide tax information
   - Verify payment method
   
2. **Threshold**:
   - Minimum $100 USD for payment
   - Payments monthly after reaching threshold

### ✅ Account Suspension Prevention:

**Common Reasons for Suspension:**
- Invalid click activity
- Content policy violations
- Copyright infringement
- Artificial traffic
- Site navigation issues

**How We Prevent This:**
- ✅ Natural, organic traffic only
- ✅ Original curation value
- ✅ Proper source attribution
- ✅ Clear site navigation
- ✅ Quality user experience

---

## Emergency Contacts & Resources

### 📞 If Issues Arise:

1. **AdSense Help Center**: https://support.google.com/adsense
2. **Policy Questions**: AdSense Help Forum
3. **Account Issues**: https://support.google.com/adsense/contact/appeal
4. **Program Policies**: https://support.google.com/adsense/answer/48182

### 📚 Key Resources:

- **AdSense Program Policies**: https://support.google.com/adsense/answer/48182
- **Webmaster Guidelines**: https://support.google.com/webmasters/answer/35769
- **Invalid Activity**: https://support.google.com/adsense/answer/16737
- **Ad Placement**: https://support.google.com/adsense/answer/1346295

---

## Nexus-Specific Compliance Checklist

### ✅ Pre-Launch Checklist:

- [x] AdSense code added to `base.html`
- [ ] Privacy policy updated with AdSense info
- [ ] Cookie consent working (Consent Manager active)
- [ ] Ad placements don't obstruct content
- [ ] Ads work on mobile and desktop
- [ ] No more than 3 ad units per page
- [ ] Ads clearly labeled as "Advertisements"
- [ ] Content adds value beyond aggregation
- [ ] All links to original sources work
- [ ] Site passes mobile-friendly test
- [ ] Page load speed acceptable with ads

### ✅ Post-Launch Monitoring:

- [ ] Check AdSense dashboard daily (first week)
- [ ] Monitor invalid click reports
- [ ] Review policy notifications
- [ ] Track earnings and RPM
- [ ] Monitor user experience
- [ ] Check ad fill rates
- [ ] Review Analytics for traffic quality

---

## Summary: Key Rules to Remember

1. **NEVER** click your own ads or ask others to click
2. **NEVER** place ads on inappropriate content
3. **NEVER** modify AdSense code
4. **ALWAYS** provide value beyond content aggregation
5. **ALWAYS** link to original sources
6. **ALWAYS** keep content appropriate and legal
7. **ALWAYS** respect user privacy and consent
8. **ALWAYS** maintain good user experience

---

**Last Reviewed:** December 1, 2025  
**Next Review:** Monthly or when policies update  
**Responsible:** Site Administrator

