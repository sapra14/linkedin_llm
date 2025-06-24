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
    text = text.translate(str.maketrans(string.punctuation, ' ' * len(string.punctuation)))
    tokens = text.split()
    return tokens


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


def filter_by_keyword(metadata, keyword, field):
    kw_tokens = normalize_and_tokenize(keyword)
    results = []
    for item in metadata:
        text_tokens = normalize_and_tokenize(item.get(field, ""))
        if all(token in text_tokens for token in kw_tokens):
            results.append(item)
    return results


def filter_by_attribute_in_description(metadata, attribute):
    attr_norm = normalize_text(attribute)
    return [item for item in metadata if attr_norm in normalize_text(item.get('description', ''))]


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


def apply_filters(metadata, question):
    q = normalize_text(question)

    # 1. Person name filter - match posts by person name in author or name fields
    # Try to extract person name after "about", "by", "details of", "for"
    m = re.search(r'(?:about|by|details of|for)\s+([\w\s]+)', q)
    if m:
        person_name = m.group(1).strip()
        person_tokens = normalize_and_tokenize(person_name)

        def match_person(post):
            author = normalize_text(post.get('author', ''))
            name = normalize_text(post.get('name', ''))
            combined = author + " " + name
            return all(token in combined for token in person_tokens)

        matched = [post for post in metadata if match_person(post)]
        if matched:
            return matched

    # 2. Numeric followers filter e.g. >3000 followers
    m = re.search(r'followers.*?(?:greater|more|above|over|>|>=)\s*(\d+)', q)
    if m:
        thr = float(m.group(1))
        return filter_by_numeric_threshold(metadata, 'followers', thr, '>')

    # 3. Attribute-based filter: role in description e.g. "backend engineer"
    m = re.search(r'(?:role|position|title|description).*?(?:is|mentions|contains|with|that mentions|with)\s*["\']?([\w\s]+)["\']?', q)
    if m:
        attr = m.group(1).strip().lower()
        return filter_by_attribute_in_description(metadata, attr)

    # 4. Keyword search in postContent
    m = re.search(r'post[s]? (?:content )?(?:mention|contain|with|about|that has)\s*["\']([^"\']+)["\']', q)
    if m:
        kw = m.group(1)
        return filter_by_keyword(metadata, kw, 'postContent')

    # 5. Date-based filter: posts from <month> <year> or posts in <month>
    m = re.search(r'posts? (?:from|in) (\w+)(?: (\d{4}))?', q)
    if m:
        month = m.group(1).capitalize()
        year = int(m.group(2)) if m.group(2) else None
        try:
            return filter_posts_in_month_year(metadata, month, year)
        except Exception:
            pass

    # 6. Multi-condition: role + followers
    m = re.search(r'(?:role|position|title).*?["\']?([\w\s]+)["\'].*followers.*?(?:greater|more|above|over|>|>=)\s*(\d+)', q)
    if m:
        role = m.group(1).strip().lower()
        thr = float(m.group(2))
        filtered = [i for i in filter_by_attribute_in_description(metadata, role) if i in filter_by_numeric_threshold(metadata, 'followers', thr, '>')]
        return filtered

    # 7. Max likeCount among articles
    if 'highest likecount' in q or 'max likecount' in q:
        articles = [i for i in metadata if normalize_text(i.get('type', '')) == 'article']
        if not articles:
            return []
        max_like = max(articles, key=lambda x: x.get('likeCount', 0))
        return [max_like]

    # 8. Specific post detail by postUrl
    m = re.search(r'posturl.*?["\']?([^"\']+)["\']?', q)
    if m:
        url = m.group(1).strip()
        return [i for i in metadata if i.get('postUrl','').strip() == url]

    # 9. Existence check in description (e.g. Microsoft and Full Stack Developer)
    m = re.findall(r'["\']([^"\']+)["\']', question)
    if len(m) >= 2:
        kw1, kw2 = m[0].lower(), m[1].lower()
        filtered = [i for i in metadata if kw1 in normalize_text(i.get('description', '')) and kw2 in normalize_text(i.get('description', ''))]
        return filtered

    # 10. Count distinct authors who have Text posts
    if 'how many' in q and 'distinct authors' in q and 'text' in q:
        count = count_distinct_authors_text_posts(metadata)
        return [{"name": f"Count of distinct authors with Text posts: {count}"}]

    # 11. Repost info by specific person
    m = re.search(r'reposted.*by\s*([\w\s]+)', q)
    if m:
        person = m.group(1).strip().lower()
        filtered = [i for i in metadata if normalize_text(i.get('author', '')) == person and i.get('repostCount', 0) > 0]
        return filtered

    # Default fallback: return top 5 posts
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
