"""
Article Scraper Service

Fetches and extracts readable article content from web pages.
Uses BeautifulSoup to parse HTML and extract main content.
"""

import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, List
import re
from urllib.parse import urlparse
from fastapi import HTTPException


class ArticleScraperService:
    """Service for scraping article content from web pages"""

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.timeout = 15  # Increased from 10 to 15 seconds for slower sites
        self.max_retries = 2  # Retry failed requests up to 2 times
        # AdSense Compliance: Limit content to excerpts only (not full articles)
        self.MAX_EXCERPT_WORDS = 300  # Safe limit for copyright and AdSense compliance
        self.MAX_EXCERPT_CHARS = 2000  # Fallback character limit

    def _validate_url(self, url: str) -> None:
        """Validate URL to prevent SSRF attacks."""
        try:
            parsed = urlparse(url)

            # Only allow http and https schemes
            if parsed.scheme not in ("http", "https"):
                raise ValueError("Invalid URL scheme")

            # Block private/internal IP ranges
            hostname = parsed.hostname
            if not hostname:
                raise ValueError("Invalid URL")

            # Block localhost and private IP ranges
            blocked_hosts = [
                "localhost",
                "127.0.0.1",
                "0.0.0.0",
                "10.",
                "172.16.",
                "172.17.",
                "172.18.",
                "172.19.",
                "172.20.",
                "172.21.",
                "172.22.",
                "172.23.",
                "172.24.",
                "172.25.",
                "172.26.",
                "172.27.",
                "172.28.",
                "172.29.",
                "172.30.",
                "172.31.",
                "192.168.",
                "169.254.",
            ]

            hostname_lower = hostname.lower()
            if any(
                hostname_lower == blocked or hostname_lower.startswith(blocked)
                for blocked in blocked_hosts
            ):
                raise ValueError("Access to internal resources is forbidden")

            # Additional check for IPv6 localhost
            if hostname_lower in ("::1", "::ffff:127.0.0.1"):
                raise ValueError("Access to internal resources is forbidden")

        except ValueError:
            raise
        except Exception:
            raise ValueError("Invalid URL format")

    def _fetch_with_retries(self, url: str) -> Optional[requests.Response]:
        """Fetch URL with retry logic"""
        last_error = None
        for attempt in range(1, self.max_retries + 2):
            try:
                response = requests.get(
                    url, headers=self.headers, timeout=self.timeout
                )
                response.raise_for_status()
                return response
            except requests.Timeout:
                last_error = f"Timeout after {self.timeout}s"
                if attempt <= self.max_retries:
                    print(f"  [RETRY {attempt}/{self.max_retries}] {last_error}")
            except requests.RequestException as e:
                last_error = str(e)
                if any(code in str(e) for code in ["429", "403", "401"]):
                    raise
                if attempt <= self.max_retries:
                    print(f"  [RETRY {attempt}/{self.max_retries}] {last_error}")
        return None

    def _process_scraped_article(self, soup: BeautifulSoup, url: str) -> Optional[Dict]:
        """Process and validate scraped article data"""
        article_data = {
            "url": url,
            "title": self._extract_title(soup),
            "content": self._extract_content(soup),
            "author": self._extract_author(soup),
            "published_date": self._extract_date(soup),
            "image_url": self._extract_image(soup, url),
            "domain": urlparse(url).netloc,
        }

        if article_data["content"] and len(article_data["content"]) > 200:
            original_length = len(article_data["content"])
            article_data["content"] = self._limit_to_excerpt(
                article_data["content"], article_data["domain"]
            )
            article_data["is_excerpt"] = True
            article_data["full_article_available"] = True
            print(
                f"✅ Successfully scraped {original_length} characters, limited to excerpt ({len(article_data['content'])} chars)"
            )
            return article_data

        print(
            f"⚠️ Content too short or empty. Length: {len(article_data['content']) if article_data['content'] else 0}"
        )
        if article_data["title"]:
            print("ℹ️ Returning article with limited content")
            article_data["content"] = "Unable to extract facts. Please visit the source site to read the full article."
            article_data["is_excerpt"] = False
            article_data["full_article_available"] = False
            return article_data
        return None

    def fetch_article(self, url: str) -> Optional[Dict]:
        """
        Fetch and parse article content from a URL.

        Args:
            url: The article URL to scrape

        Returns:
            Dict with title, content, author, date, and image_url if successful
            None if scraping fails
        """
        try:
            print(f"📰 Fetching article from: {url}")

            # Validate URL to prevent SSRF
            self._validate_url(url)

            # Attempt fetch with retries
            response = self._fetch_with_retries(url)

            if not response:
                print(f"❌ Failed to fetch after {self.max_retries + 1} attempts")
                return None

            # Parse HTML
            soup = BeautifulSoup(response.content, "html.parser")
            return self._process_scraped_article(soup, url)
                return None

        except requests.exceptions.ConnectionError as e:
            print(f"❌ Connection error scraping article: {e}")
            return None
        except requests.exceptions.Timeout:
            print(f"❌ Timeout scraping article after {self.timeout}s")
            return None
        except Exception as e:
            print(f"❌ Error scraping article: {e}")
            import traceback

            print(f"   Exception type: {type(e).__name__}")
            return None

    def _limit_to_excerpt(self, content: str, domain: str) -> str:
        """
        Extract and condense key facts from article content.
        Intelligently summarizes content to ~300 words of key ideas rather than truncating.

        Args:
            content: Full article content
            domain: Source domain (affects extraction strategy)

        Returns:
            Condensed key facts as bullet points or summarized excerpt
        """
        # For all articles, extract important sentences and condense them
        sentences = re.split(r"(?<=[.!?])\s+", content)

        # If very short content, return as-is
        if len(sentences) <= 3:
            return content

        # Score each sentence for importance
        scored_sentences = []
        for sentence in sentences:
            if len(sentence.strip()) < 20:  # Skip very short sentences
                continue

            score = self._score_sentence_importance(sentence)
            scored_sentences.append((score, sentence.strip()))

        # Sort by score and extract top facts
        scored_sentences.sort(reverse=True, key=lambda x: x[0])

        # Extract enough facts to reach ~300 words, prioritizing importance
        extracted_facts = []
        word_count = 0
        target_words = 300

        for score, sentence in scored_sentences:
            sentence_words = len(sentence.split())
            # Allow going over if it's an important sentence and we're under 400 words
            if word_count < target_words or (score > 1.5 and word_count < 400):
                extracted_facts.append(sentence)
                word_count += sentence_words
            elif word_count >= target_words:
                # Once we exceed target, only add very high-scoring facts
                if score > 3.0 and word_count < 450:
                    extracted_facts.append(sentence)
                    word_count += sentence_words
                else:
                    break

        # Re-sort by original order in document (maintain narrative flow)
        fact_sentences_set = set(extracted_facts)
        ordered_facts = []
        for sentence in sentences:
            if sentence.strip() in fact_sentences_set:
                ordered_facts.append(sentence.strip())

        # Format as bullet points
        if ordered_facts:
            facts_text = "\n\n".join([f"• {fact}" for fact in ordered_facts])
            return facts_text

        # Fallback to first 300 words if extraction fails
        words = content.split()
        return " ".join(words[: self.MAX_EXCERPT_WORDS])

    def _score_sentence_importance(self, sentence: str) -> float:
        """
        Score a sentence based on importance indicators.

        Args:
            sentence: Sentence to score

        Returns:
            Importance score (higher = more important)
        """
        score = 0.0
        sentence_lower = sentence.lower()

        # 1. Contains numbers/statistics (high value)
        if re.search(
            r"\d+[\d,\.]*\s*(?:%|percent|million|billion|thousand|dollars?|years?)",
            sentence_lower,
        ):
            score += 3.0
        elif re.search(r"\d+", sentence):
            score += 1.5

        # 2. Contains quotes (direct information)
        if any(q in sentence for q in ['"', '"', "'", "'"]):
            score += 2.5

        # 3. Contains key action words
        action_words = [
            "announced",
            "revealed",
            "confirmed",
            "discovered",
            "found",
            "reported",
            "stated",
            "said",
            "according to",
            "will",
            "plans to",
            "launches",
            "released",
            "unveiled",
            "introduces",
            "shows",
        ]
        for word in action_words:
            if word in sentence_lower:
                score += 2.0
                break

        # 4. Contains named entities (people, places, organizations)
        # Simple heuristic: capitalized words (excluding start of sentence)
        words = sentence.split()
        if len(words) > 1:
            caps_count = sum(
                1 for word in words[1:] if word and word[0].isupper() and len(word) > 2
            )
            score += min(caps_count * 0.5, 2.0)  # Cap at 2.0

        # 5. Contains temporal information (when things happened/will happen)
        time_indicators = [
            "today",
            "yesterday",
            "tomorrow",
            "this week",
            "last month",
            "next year",
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
            "july",
            "august",
            "september",
            "october",
            "november",
            "december",
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "2024",
            "2025",
        ]
        for indicator in time_indicators:
            if indicator in sentence_lower:
                score += 1.0
                break

        # 6. Sentence position bonus (first few sentences often important)
        # This will be applied by caller if needed

        # 7. Length penalty (too short or too long sentences less important)
        word_count = len(words)
        if word_count < 8:
            score -= 1.0
        elif word_count > 50:
            score -= 0.5
        elif 15 <= word_count <= 30:  # Sweet spot
            score += 0.5

        return score

    def _get_instant_answer_from_api(
        self, api_data: Dict
    ) -> tuple[Optional[str], Optional[str]]:
        """Extract instant answer and image from API response"""
        instant_answer = None
        image_url = None

        # Abstract is the main description (like Wikipedia excerpt)
        abstract = api_data.get("Abstract", "").strip()
        if abstract:
            instant_answer = abstract
            image_url = api_data.get("Image", "")

        # If no abstract, try Definition
        if not instant_answer:
            definition = api_data.get("Definition", "").strip()
            if definition:
                instant_answer = definition

        return instant_answer, image_url

    def _build_context_from_api(
        self, api_data: Dict, query: str, instant_answer: Optional[str]
    ) -> List[str]:
        """Build context parts from API data"""
        context_parts = []

        if instant_answer:
            context_parts.append(f"**{query}**\n")
            context_parts.append(instant_answer)

            # Add source if available
            source = api_data.get("AbstractSource", "")
            if source:
                context_parts.append(f"\n\n*Source: {source}*")

            context_parts.append("\n" + "=" * 50)

        # Add related topics if available
        related_topics = api_data.get("RelatedTopics", [])
        if related_topics:
            context_parts.append("\n\n**Related Information:**\n")
            for i, topic in enumerate(related_topics[:5], 1):
                if isinstance(topic, dict):
                    text = topic.get("Text", "")
                    if text:
                        context_parts.append(f"{i}. {text}")

        return context_parts

    def fetch_search_context(self, url: str) -> Optional[Dict]:
        """
        Fetch and parse search results from DuckDuckGo to provide context.
        Extracts instant answer boxes and top search results.
        Uses DuckDuckGo's Instant Answer API for rich content.

        Args:
            url: The DuckDuckGo search URL

        Returns:
            Dict with search results and context if successful
            None if scraping fails
        """
        try:
            print(f"🔍 Fetching search context from: {url}")

            # Extract search query from URL
            from urllib.parse import urlparse, parse_qs

            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            query = params.get("q", ["unknown"])[0]

            # Use DuckDuckGo's Instant Answer API
            # This is a free, public API that doesn't require authentication
            api_url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1"

            print(f"📡 Querying DuckDuckGo API: {api_url}")
            api_response = requests.get(
                api_url, headers=self.headers, timeout=self.timeout
            )
            api_response.raise_for_status()
            api_data = api_response.json()

            # Extract instant answer content
            instant_answer, image_url = self._get_instant_answer_from_api(api_data)

            # Build context
            context_parts = []

            if instant_answer:
                context_parts = self._build_context_from_api(
                    api_data, query, instant_answer
                )
            else:
                # No instant answer from API - scrape HTML page
                print(f"⚠️ No instant answer from API, scraping HTML for '{query}'")
                html_data = self._scrape_search_html(url, query)
                if html_data:
                    return html_data

                # If HTML scraping also failed, provide fallback
                context_parts.append(f"**{query}**\n")
                context_parts.append("No detailed information available.")
                context_parts.append(
                    "\n\nThis query may require direct searching on DuckDuckGo."
                )

            content = (
                "\n".join(context_parts) if context_parts else "No information found."
            )

            search_data = {
                "url": url,
                "title": query,
                "content": content,
                "author": "DuckDuckGo",
                "published_date": "",
                "image_url": image_url if image_url and len(image_url) > 10 else None,
                "domain": "duckduckgo.com",
                "search_results": [],
                "instant_answer": instant_answer,
            }

            print(
                f"✅ Extracted instant answer: {bool(instant_answer)}, Image: {bool(image_url)}"
            )
            return search_data

        except Exception as e:
            print(f"❌ Error scraping search results: {e}")
            import traceback

            traceback.print_exc()
            return None

    def _extract_answer_box(self, soup: BeautifulSoup, query: str) -> List[str]:
        """Extract featured snippet / answer box from HTML"""
        context_parts = [f"**{query}**\n"]

        answer_selectors = [
            ("div", {"class": re.compile("module__text|zci")}),
            ("div", {"id": "zero_click_abstract"}),
            ("div", {"class": "result__snippet--d"}),
        ]

        for tag, attrs in answer_selectors:
            answer_box = soup.find(tag, attrs)
            if answer_box:
                snippet_text = answer_box.get_text(strip=True, separator=" ")
                if snippet_text and len(snippet_text) > 30:
                    context_parts.append(f"{snippet_text}\n")
                    context_parts.append("=" * 50)
                    break

        return context_parts

    def _extract_search_result_item(
        self, result
    ) -> tuple[Optional[str], Optional[str]]:
        """Extract title and snippet from a single search result"""
        # Extract title
        title_elem = (
            result.find("h2")
            or result.find("a", class_=re.compile("result__a|result__title"))
            or result.find("a")
        )

        title = title_elem.get_text(strip=True) if title_elem else None

        # Extract snippet/description
        snippet_elem = (
            result.find("span", class_=re.compile("result__snippet"))
            or result.find("div", class_=re.compile("result__snippet|snippet"))
            or result.find("p")
        )
        snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

        return title, snippet

    def _extract_search_results(self, soup: BeautifulSoup) -> tuple[List[str], bool]:
        """Extract search results from HTML"""
        context_parts = []
        results_found = False

        # Try modern DuckDuckGo result selectors
        results = soup.find_all("article", limit=5)
        if not results:
            results = soup.find_all("div", class_=re.compile("result__"), limit=5)
        if not results:
            results = soup.find_all("li", class_=re.compile("result"), limit=5)

        if results:
            context_parts.append("\n**Search Results:**\n")
            for i, result in enumerate(results, 1):
                title, snippet = self._extract_search_result_item(result)

                if title:
                    context_parts.append(f"\n{i}. **{title}**")
                    if snippet and len(snippet) > 20:
                        context_parts.append(f"   {snippet[:200]}")
                    results_found = True

        return context_parts, results_found

    def _scrape_search_html(self, url: str, query: str) -> Optional[Dict]:
        """
        Scrape DuckDuckGo HTML page when API returns no instant answer.
        Extracts search results and snippets from the HTML.
        """
        try:
            print(f"🌐 Scraping HTML from: {url}")

            # Validate URL to prevent SSRF
            self._validate_url(url)

            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            # Extract answer box
            context_parts = self._extract_answer_box(soup, query)

            # Extract search results
            result_parts, results_found = self._extract_search_results(soup)
            context_parts.extend(result_parts)

            # If we got no useful content, return None
            if not results_found and len(context_parts) <= 1:
                print(f"⚠️ No content extracted from HTML for '{query}'")
                return None

            content = "\n".join(context_parts)

            search_data = {
                "url": url,
                "title": query,
                "content": content,
                "author": "DuckDuckGo",
                "published_date": "",
                "image_url": None,
                "domain": "duckduckgo.com",
                "search_results": [],
                "instant_answer": None,
            }

            print("✅ Extracted search results from HTML")
            return search_data

        except Exception as e:
            print(f"❌ Error scraping HTML: {e}")
            import traceback

            traceback.print_exc()
            return None

    def _extract_search_query(self, soup: BeautifulSoup, url: str) -> str:
        """Extract search query from page or URL"""
        # Try to get from URL parameter
        from urllib.parse import urlparse, parse_qs

        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        if "q" in params:
            return params["q"][0]

        # Fallback: try to find on page
        query_input = soup.find("input", {"name": "q"})
        if query_input and query_input.get("value"):
            return query_input.get("value")

        return "unknown query"

    def _try_extract_from_selector(
        self, soup: BeautifulSoup, tag: str, selector_pattern: str, min_length: int = 50
    ) -> Optional[str]:
        """Try to extract text from a specific selector"""
        element = soup.find(tag, class_=re.compile(selector_pattern))
        if element:
            text = element.get_text(separator=" ", strip=True)
            if text and len(text) > min_length:
                return text
        return None

    def _try_extract_from_attrs(
        self, soup: BeautifulSoup, tag: str, attrs: dict, min_length: int = 50
    ) -> Optional[str]:
        """Try to extract text from element with specific attributes"""
        element = soup.find(tag, attrs=attrs)
        if element:
            text = element.get_text(separator=" ", strip=True)
            if text and len(text) > min_length:
                return text
        return None

    def _extract_instant_answer(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract instant answer/infobox from search results.
        This includes Wikipedia snippets, knowledge panels, etc.
        """
        # Try DuckDuckGo instant answer box
        result = self._try_extract_from_selector(
            soup, "div", "module__text|zci-wrapper|ia-module"
        )
        if result:
            return result

        # Wikipedia/knowledge panel content
        kb_panel = soup.find("div", attrs={"data-area": "infobox"})
        if not kb_panel:
            kb_panel = soup.find("div", class_=re.compile("infobox|knowledge-panel"))

        if kb_panel:
            # Get the main text description
            description = kb_panel.find(
                "div", class_=re.compile("description|text|content")
            )
            if description:
                text = description.get_text(separator=" ", strip=True)
                if text and len(text) > 50:
                    return text

        # Try to find any prominent description or snippet at top of results
        result = self._try_extract_from_selector(
            soup, "div", "result--zero-click|abstract|answer"
        )
        if result:
            return result

        # Look for any highlighted/featured content
        featured = soup.find(
            ["div", "section"], class_=re.compile("featured|highlight|instant")
        )
        if featured:
            text = featured.get_text(separator=" ", strip=True)
            if text and len(text) > 50:
                return text

        return None

    def _extract_search_results(self, soup: BeautifulSoup) -> list:
        """Extract search results from DuckDuckGo page"""
        results = []

        # DuckDuckGo result selectors (may need adjustment)
        result_divs = soup.find_all("article", {"data-testid": re.compile("result")})
        if not result_divs:
            result_divs = soup.find_all("div", class_=re.compile("result"))

        for result_div in result_divs[:10]:  # Get top 10
            try:
                # Extract title
                title_elem = result_div.find("h2") or result_div.find(
                    "a", class_=re.compile("result__a")
                )
                title = title_elem.get_text().strip() if title_elem else ""

                # Extract snippet/description
                snippet_elem = result_div.find(
                    "div", class_=re.compile("snippet|result__snippet")
                )
                if not snippet_elem:
                    # Try finding any div with text
                    snippet_elem = result_div.find(
                        "span", class_=re.compile("result__snippet")
                    )
                snippet = snippet_elem.get_text().strip() if snippet_elem else ""

                # Extract URL
                link_elem = result_div.find("a", href=True)
                link = link_elem["href"] if link_elem else ""

                if title:  # Only add if we have at least a title
                    results.append({"title": title, "snippet": snippet, "url": link})
            except Exception as e:
                print(f"⚠️ Error parsing individual result: {e}")
                continue

        return results

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract article title"""
        # Try multiple selectors
        selectors = [
            ("meta", {"property": "og:title"}),
            ("meta", {"name": "twitter:title"}),
            "h1",
            ("h1", {"class": re.compile("title|headline", re.I)}),
            "title",
        ]

        for selector in selectors:
            if isinstance(selector, tuple):
                tag, attrs = selector
                element = soup.find(tag, attrs)
                if element:
                    return element.get("content", element.get_text().strip())
            else:
                element = soup.find(selector)
                if element:
                    return element.get_text().strip()

        return "Article"

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main article content"""
        # Remove script, style, nav, footer, etc.
        for element in soup(
            ["script", "style", "nav", "footer", "header", "aside", "iframe"]
        ):
            element.decompose()

        # Try to find article content container
        content_selectors = [
            ("article", {}),
            ("div", {"class": re.compile("article|content|post|entry", re.I)}),
            ("div", {"id": re.compile("article|content|post|entry", re.I)}),
            ("main", {}),
        ]

        article_element = None
        for tag, attrs in content_selectors:
            article_element = soup.find(tag, attrs)
            if article_element:
                break

        if not article_element:
            # Fallback: use body
            article_element = soup.find("body")

        if not article_element:
            return ""

        # Extract paragraphs
        paragraphs = []
        for p in article_element.find_all("p"):
            text = p.get_text().strip()
            # Filter out very short paragraphs (likely navigation/footer text)
            if len(text) > 50:
                paragraphs.append(text)

        content = "\n\n".join(paragraphs)

        return content

    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article author"""
        # Try multiple selectors
        selectors = [
            ("meta", {"name": "author"}),
            ("meta", {"property": "article:author"}),
            ("span", {"class": re.compile("author", re.I)}),
            ("a", {"class": re.compile("author", re.I)}),
            ("div", {"class": re.compile("author", re.I)}),
        ]

        for selector in selectors:
            if isinstance(selector, tuple):
                tag, attrs = selector
                element = soup.find(tag, attrs)
                if element:
                    return element.get("content", element.get_text().strip())

        return None

    def _extract_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract publication date"""
        selectors = [
            ("meta", {"property": "article:published_time"}),
            ("meta", {"name": "publish-date"}),
            ("time", {}),
            ("span", {"class": re.compile("date|time", re.I)}),
        ]

        for selector in selectors:
            if isinstance(selector, tuple):
                tag, attrs = selector
                element = soup.find(tag, attrs)
                if element:
                    return (
                        element.get("content")
                        or element.get("datetime")
                        or element.get_text().strip()
                    )

        return None

    def _make_absolute_url(self, img_url: str, base_url: str) -> str:
        """Convert relative URLs to absolute"""
        if img_url.startswith("//"):
            return "https:" + img_url
        if img_url.startswith("/"):
            parsed = urlparse(base_url)
            return f"{parsed.scheme}://{parsed.netloc}{img_url}"
        return img_url

    def _is_placeholder_image(self, img_url: str) -> bool:
        """Check if image is likely a small placeholder"""
        placeholder_patterns = [
            r"150x150", r"150[_-]150", r"100x100", r"100[_-]100",
            r"thumbnail", r"thumb", r"avatar", r"icon",
        ]
        url_lower = img_url.lower()
        return any(re.search(pattern, url_lower) for pattern in placeholder_patterns)

    def _extract_image_from_meta_tags(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Try to extract image from meta tags"""
        selectors = [
            ("meta", {"property": "og:image"}),
            ("meta", {"name": "twitter:image"}),
        ]
        for tag, attrs in selectors:
            element = soup.find(tag, attrs)
            if element:
                img_url = element.get("content")
                if img_url:
                    img_url = self._make_absolute_url(img_url, base_url)
                    if not self._is_placeholder_image(img_url):
                        return img_url
                    print(f"⚠️ Rejected placeholder meta image: {img_url}")
        return None

    def _extract_image_from_article_body(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Look for large image in article body"""
        article_element = (
            soup.find("article")
            or soup.find("main")
            or soup.find("div", {"class": re.compile("article|content|post", re.I)})
        )
        if not article_element:
            return None

        for img in article_element.find_all("img", limit=5):
            img_url = img.get("src") or img.get("data-src")
            if img_url:
                img_url = self._make_absolute_url(img_url, base_url)
                if not self._is_placeholder_image(img_url):
                    print(f"✅ Found article body image: {img_url}")
                    return img_url
        return None

    def _extract_image(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Extract main article image, filtering out small placeholder images"""
        img_url = self._extract_image_from_meta_tags(soup, base_url)
        if img_url:
            return img_url
        return self._extract_image_from_article_body(soup, base_url)

    def download_and_optimize_image(
        self, image_url: str, content_id: int
    ) -> Optional[str]:
        """
        Download image from URL and optimize it for storage.

        Args:
            image_url: URL of the image to download
            content_id: ID of the content item for filename

        Returns:
            Local path to optimized image if successful, None otherwise
        """
        try:
            from PIL import Image
            from io import BytesIO
            import os

            # Validate URL
            self._validate_url(image_url)

            # Download image
            response = requests.get(image_url, headers=self.headers, timeout=10)
            response.raise_for_status()

            # Open and optimize image
            img = Image.open(BytesIO(response.content))

            # Convert RGBA to RGB if needed
            if img.mode in ("RGBA", "LA", "P"):
                rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                rgb_img.paste(
                    img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None
                )
                img = rgb_img

            # Resize to display size
            img.thumbnail((480, 270), Image.Resampling.LANCZOS)

            # Create storage directory
            image_dir = os.path.join(
                os.path.dirname(__file__), "..", "static", "images", "articles"
            )
            os.makedirs(image_dir, exist_ok=True)

            # Save optimized image
            filename = f"article_{content_id}.jpg"
            filepath = os.path.join(image_dir, filename)
            img.save(filepath, "JPEG", quality=85, optimize=True)

            # Return relative path for serving
            return f"/static/images/articles/{filename}"

        except Exception as e:
            print(f"❌ Failed to download/optimize image {image_url}: {e}")
            return None


# Global instance
article_scraper = ArticleScraperService()
