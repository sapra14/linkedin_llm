import re
import string
from datetime import datetime
from dateutil.parser import parse as dateparse
from unidecode import unidecode
import json
from collections import Counter

# ----------------------------
# Text normalization utilities
# ----------------------------

def normalize_text(text):
    if not text:
        return ""
    return unidecode(text).lower().strip()

def normalize_and_tokenize(text):
    if not text:
        return []
    text = unidecode(text).lower()
    text = text.translate(str.maketrans(string.punctuation, ' ' * len(string.punctuation)))
    return text.split()

# ----------------------------
# Filtering functions
# ----------------------------

def filter_by_field(metadata, field, value, exact=False):
    value_norm = normalize_text(value)
    results = []
    for item in metadata:
        item_val = normalize_text(str(item.get(field, "")))
        if exact and item_val == value_norm:
            results.append(item)
        elif not exact and value_norm in item_val:
            results.append(item)
    return results

def filter_by_author(metadata, author_name):
    author_norm = normalize_text(author_name)
    return [post for post in metadata if author_norm in normalize_text(post.get('author', ''))]

def filter_by_post_url(metadata, url_fragment):
    url_fragment = normalize_text(url_fragment)
    return [item for item in metadata if url_fragment in normalize_text(item.get('postUrl', ''))]

def filter_by_keyword_in_post_content(metadata, keyword):
    keyword = normalize_text(keyword)
    return [item for item in metadata if keyword in normalize_text(item.get('postContent', ''))]

def filter_by_attribute_in_description(metadata, attribute):
    attr_norm = normalize_text(attribute)
    return [item for item in metadata if attr_norm in normalize_text(item.get('description', ''))]

def filter_by_numeric_threshold(metadata, field, threshold, op='>'):
    results = []
    for item in metadata:
        val_str = str(item.get(field, "")).replace('+', '').replace(',', '').strip()
        try:
            val = float(re.findall(r'[\d.]+', val_str)[0])
        except Exception:
            continue
        if (op == '>' and val > threshold) or (op == '>=' and val >= threshold) or \
           (op == '<' and val < threshold) or (op == '<=' and val <= threshold):
            results.append(item)
    return results

def filter_posts_in_month_year(metadata, month_name, year=None):
    try:
        month_num = datetime.strptime(month_name, "%B").month if month_name else None
    except Exception:
        return []
    results = []
    for item in metadata:
        post_date = item.get('postDate', '')
        try:
            dt = dateparse(post_date, fuzzy=True)
            if dt.month == month_num and (year is None or dt.year == year):
                results.append(item)
        except Exception:
            continue
    return results

def count_distinct_authors_text_posts(metadata):
    text_posts = [i for i in metadata if normalize_text(i.get('type', '')) == 'text']
    distinct_authors = set(i.get('author', '') for i in text_posts)
    return len(distinct_authors)

# ----------------------------
# Core logic to apply question-based filters
# ----------------------------

def apply_filters(metadata, question):
    q = normalize_text(question)

    # 1. Check if question asks about a person’s posts/details using common phrases
    m_person = re.search(r'(?:post details of|posts shared by|posts by|post by|posts of|post of|posts from|post from|details about posts of)\s+([\w\s]+)', q)
    if m_person:
        person_name = m_person.group(1).strip()
        matched_posts = filter_by_author(metadata, person_name)
        if matched_posts:
            return matched_posts

    # 2. Followers filter
    m_followers = re.search(r'followers.*?(?:greater|more|above|over|>|>=)\s*(\d+)', q)
    if m_followers:
        thr = float(m_followers.group(1))
        return filter_by_numeric_threshold(metadata, 'followers', thr, '>')

    # 3. Role/title in description
    m_role = re.search(r'(?:role|position|title|description).*?(?:is|mentions|contains|with|that mentions|with)\s*["\']?([\w\s]+)["\']?', q)
    if m_role:
        attr = m_role.group(1).strip().lower()
        return filter_by_attribute_in_description(metadata, attr)

    # 4. Exact quoted keyword in post content
    m_kw = re.search(r'post[s]? (?:content )?(?:mention|contain|with|about|that has)?\s*[\'"]([^\'"]+)[\'"]', q)
    if m_kw:
        kw = m_kw.group(1)
        return filter_by_keyword_in_post_content(metadata, kw)

    # 5. Posts from a month/year
    m_date = re.search(r'posts? (?:from|in) (\w+)(?: (\d{4}))?', q)
    if m_date:
        month = m_date.group(1).capitalize()
        year = int(m_date.group(2)) if m_date.group(2) else None
        return filter_posts_in_month_year(metadata, month, year)

    # 6. Role + followers
    m_role_fol = re.search(r'(?:role|position|title).*?["\']?([\w\s]+)["\'].*followers.*?(?:greater|more|above|over|>|>=)\s*(\d+)', q)
    if m_role_fol:
        role = m_role_fol.group(1).strip().lower()
        thr = float(m_role_fol.group(2))
        filtered = [i for i in filter_by_attribute_in_description(metadata, role) if i in filter_by_numeric_threshold(metadata, 'followers', thr, '>')]
        return filtered

    # 7. Post with max likes
    if re.search(r'(most|highest|max).*like', q):
        def parse_likes(post):
            val = post.get('likeCount', 0)
            try:
                return float(str(val).replace(",", "").replace("+", "").strip())
            except:
                return 0

        filtered_posts = [post for post in metadata if parse_likes(post) > 0]
        if not filtered_posts:
            return []

        max_likes = max(parse_likes(post) for post in filtered_posts)
        for post in filtered_posts:
            if parse_likes(post) == max_likes:
                return [post]

    # 8. Post with max comments
    if re.search(r'(most|highest|max).*comment', q):
        def parse_comments(post):
            val = post.get('commentCount', 0)
            try:
                return float(str(val).replace(",", "").replace("+", "").strip())
            except:
                return 0

        filtered_posts = [post for post in metadata if parse_comments(post) > 0]
        if not filtered_posts:
            return []

        max_comments = max(parse_comments(post) for post in filtered_posts)
        for post in filtered_posts:
            if parse_comments(post) == max_comments:
                return [post]

    # 9. Specific post URL
    m_url = re.search(r'posturl.*?["\']?([^"\']+)["\']?', q)
    if m_url:
        url = m_url.group(1).strip()
        return [i for i in metadata if i.get('postUrl', '').strip() == url]

    # 10. Count distinct authors with text posts
    if 'how many' in q and 'distinct authors' in q and 'text' in q:
        count = count_distinct_authors_text_posts(metadata)
        return [{"name": f"Count of distinct authors with Text posts: {count}"}]

    # 11. Fallback: keyword search in post content, but avoid common stopwords
    stopwords = {
        'give', 'me', 'details', 'of', 'the', 'which', 'that', 'has', 'have', 'mention',
        'mentions', 'post', 'posts', 'content', 'show', 'display', 'with', 'who', 'whose',
        'what', 'is', 'in', 'and', 'or', 'a', 'an', 'by', 'for', 'from', 'about'
    }
    question_tokens = normalize_and_tokenize(question)
    keywords = [token for token in question_tokens if token not in stopwords and len(token) > 2]

    if keywords:
        def keyword_match(post):
            post_tokens = normalize_and_tokenize(post.get('postContent', ''))
            return any(token in post_tokens for token in keywords)
        fallback_results = [post for post in metadata if keyword_match(post)]
        if fallback_results:
            return fallback_results

    return []

# ----------------------------
# Output formatter
# ----------------------------

def format_results(posts):
    if not posts:
        return "🚫 No matching results found."

    if "Count of distinct authors" in posts[0].get("name", ""):
        return f"📊 {posts[0]['name']}"

    results = []
    for post in posts:
        block = f"""
👤 **Name**: {post.get('name', 'N/A')}
🔗 **Profile URL**: {post.get('profile_url', 'N/A')}
👥 **Followers**: {post.get('followers', 'N/A')}

📝 **Post Content**:
{post.get('postContent', 'N/A')}

📎 **Post URL**: {post.get('postUrl', 'N/A')}
📅 **Post Date**: {post.get('postDate', 'N/A')}
📌 **Type**: {post.get('type', 'N/A')}
👍 **Likes**: {post.get('likeCount', 'N/A')} | 💬 **Comments**: {post.get('commentCount', 'N/A')} | 🔁 **Reposts**: {post.get('repostCount', 'N/A')}

👤 **Author**: {post.get('author', 'N/A')} ([LinkedIn]({post.get('authorUrl', '#')}))
        """.strip()
        results.append(block)

    return "\n\n---\n\n".join(results)
