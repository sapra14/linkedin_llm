import re
import string
from datetime import datetime
from dateutil.parser import parse as dateparse
from unidecode import unidecode

def normalize_text(text):
    if not text:
        return ""
    return unidecode(text).lower().strip()

def normalize_and_tokenize(text):
    if not text:
        return []
    text = unidecode(text).lower()
    text = text.translate(str.maketrans(string.punctuation, ' '*len(string.punctuation)))
    return text.split()

def filter_by_keyword(metadata, keyword, field):
    kw_tokens = normalize_and_tokenize(keyword)
    results = []
    for item in metadata:
        text_tokens = normalize_and_tokenize(item.get(field, ""))
        if all(token in text_tokens for token in kw_tokens):
            results.append(item)
    return results

def filter_by_author(metadata, author_name):
    query = normalize_text(author_name)
    return [item for item in metadata if query in normalize_text(item.get("author", "")) or query in normalize_text(item.get("name", ""))]

def filter_by_numeric_threshold(metadata, field, threshold, op='>'):
    results = []
    for item in metadata:
        val_str = str(item.get(field, "")).replace('+', '').replace(',', '').strip()
        try:
            val = float(re.findall(r'[\d.]+', val_str)[0])
        except Exception:
            continue
        if (op == '>' and val > threshold) or \
           (op == '>=' and val >= threshold) or \
           (op == '<' and val < threshold) or \
           (op == '<=' and val <= threshold):
            results.append(item)
    return results

def filter_by_attribute_in_description(metadata, attribute):
    attr_norm = normalize_text(attribute)
    return [item for item in metadata if attr_norm in normalize_text(item.get('description', ''))]

def filter_posts_in_month_year(metadata, month_name, year=None):
    month_num = datetime.strptime(month_name, "%B").month if month_name else None
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

def apply_filters(metadata, question):
    q = normalize_text(question)

    # 1. Author name
    m = re.search(r"(?:details about|information on|posts by)\s+(.*)", q)
    if m:
        author_name = m.group(1).strip()
        return filter_by_author(metadata, author_name)

    # 2. Followers filter
    m = re.search(r'followers.*?(?:greater|more|above|over|>|>=)\s*(\d+)', q)
    if m:
        thr = float(m.group(1))
        return filter_by_numeric_threshold(metadata, 'followers', thr, '>')

    # 3. Post content keyword
    m = re.search(r'post[s]? (?:mention|contain|with|about|that has)\s*["\']?([^"\']+)["\']?', q)
    if m:
        kw = m.group(1)
        return filter_by_keyword(metadata, kw, 'postContent')

    # 4. Date filter
    m = re.search(r'posts? (?:from|in) (\w+)(?: (\d{4}))?', q)
    if m:
        month = m.group(1).capitalize()
        year = int(m.group(2)) if m.group(2) else None
        return filter_posts_in_month_year(metadata, month, year)

    # 5. Text posts count
    if 'how many' in q and 'distinct authors' in q and 'text' in q:
        count = count_distinct_authors_text_posts(metadata)
        return [{"name": f"Count of distinct authors with Text posts: {count}"}]

    # 6. Highest likeCount post
    if 'highest likecount' in q or 'max likecount' in q:
        articles = [i for i in metadata if normalize_text(i.get('type', '')) == 'article']
        if not articles:
            return []
        max_like = max(articles, key=lambda x: x.get('likeCount', 0))
        return [max_like]

    # Fallback
    return metadata[:5]

def format_results(posts):
    if not posts:
        return "No matching results found."

    if "Count of distinct authors" in posts[0].get("name", ""):
        return f"📊 {posts[0]['name']}"

    results = []
    for post in posts:
        block = f"""
👤 **Name**: {post.get('name', 'N/A')}
🔗 **Profile URL**: [{post.get('profile_url', 'N/A')}]({post.get('profile_url', 'N/A')})
👥 **Followers**: {post.get('followers', 'N/A')}

📝 **Post Content**:
{post.get('postContent', 'N/A')}

📎 **Post URL**: [{post.get('postUrl', 'N/A')}]({post.get('postUrl', 'N/A')})
📅 **Post Date**: {post.get('postDate', 'N/A')}
📌 **Type**: {post.get('type', 'N/A')}
👍 **Likes**: {post.get('likeCount', 'N/A')} | 💬 **Comments**: {post.get('commentCount', 'N/A')} | 🔁 **Reposts**: {post.get('repostCount', 'N/A')}

👤 **Author**: {post.get('author', 'N/A')} ([LinkedIn]({post.get('authorUrl', '#')}))
"""
        results.append(block.strip())

    return "\n\n---\n\n".join(results)
