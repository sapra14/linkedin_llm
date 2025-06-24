import re
import string
from unidecode import unidecode
from collections import Counter

# --- Utility functions ---

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

# --- Metadata filtering ---

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

def filter_by_post_url(metadata, url_fragment):
    url_fragment = normalize_text(url_fragment)
    return [item for item in metadata if url_fragment in normalize_text(item.get('postUrl', ''))]

def filter_by_keyword_in_post_content(metadata, keyword):
    keyword = normalize_text(keyword)
    return [item for item in metadata if keyword in normalize_text(item.get('postContent', ''))]

def filter_by_author(metadata, author_name):
    return filter_by_field(metadata, 'author', author_name)

def filter_by_name(metadata, name):
    return filter_by_field(metadata, 'name', name)

def get_most_common_post_type(metadata):
    types = [normalize_text(post.get('type', '')) for post in metadata if post.get('type')]
    if not types:
        return None
    most_common = Counter(types).most_common(1)
    return most_common[0][0] if most_common else None

def calculate_average_likecount(metadata):
    likes = []
    for post in metadata:
        val = str(post.get('likeCount', '')).replace('+', '').replace(',', '').strip()
        try:
            likes.append(float(val))
        except:
            continue
    if not likes:
        return None
    return sum(likes) / len(likes)

# --- Main function to interpret query and answer ---

def answer_linkedin_query(metadata, question):
    q = normalize_text(question)

    # 0. Profile details by person name, e.g. "give me profile details of Madhuri Jain"
    m = re.search(r'profile details of ([\w\s]+)', q)
    if m:
        person = m.group(1).strip()
        matched = filter_by_name(metadata, person)
        if matched:
            p = matched[0]
            name = p.get('name', 'N/A')
            title = p.get('description', p.get('title', 'N/A'))
            followers = p.get('followers', 'N/A')
            profile_url = p.get('profileUrl', p.get('profile_url', 'N/A'))
            return (
                f"Profile details for {person.title()}:\n"
                f"- Name: {name}\n"
                f"- Title: {title}\n"
                f"- Followers: {followers}\n"
                f"- Profile URL: {profile_url}"
            )
        else:
            return f"No profile details found for '{person}'."

    # 1. Name and title by profile URL
    m = re.search(r'name and title.*profile url[^\w]*(https?://[^\s]+)', q)
    if m:
        url = m.group(1)
        matched = filter_by_post_url(metadata, url)
        if matched:
            p = matched[0]
            name = p.get('name', 'N/A')
            title = p.get('description', p.get('title', 'N/A'))
            return f"The person's name and title is '{name} - {title}'."

    # 2. Followers count by person name
    m = re.search(r'how many followers does ([\w\s]+) have', q)
    if m:
        person = m.group(1)
        matched = filter_by_name(metadata, person)
        if matched:
            followers = matched[0].get('followers', 'N/A')
            return f"{person.title()} has '{followers}' followers."

    # 3. Post content by postUrl
    m = re.search(r'postcontent.*posturl[^\w]*(https?://[^\s]+)', q)
    if m:
        url = m.group(1)
        matched = filter_by_post_url(metadata, url)
        if matched:
            content = matched[0].get('postContent', 'N/A')
            url_ = matched[0].get('postUrl', 'N/A')
            return f"The `postContent` is '{content}'\n🔗 Post URL: {url_}"

    # 4. Type of post by URL
    m = re.search(r'type of post.*(https?://[^\s]+)', q)
    if m:
        url = m.group(1)
        matched = filter_by_post_url(metadata, url)
        if matched:
            post_type = matched[0].get('type', 'N/A')
            return f"The post is of type '{post_type}'."

    # 5. LikeCount by author and postUrl
    m = re.search(r'likecount.*post authored by ([\w\s]+).*posturl[^\w]*(https?://[^\s]+)', q)
    if m:
        author = m.group(1)
        url = m.group(2)
        candidates = filter_by_post_url(metadata, url)
        candidates = [c for c in candidates if normalize_text(c.get('author', '')) == normalize_text(author)]
        if candidates:
            likecount = candidates[0].get('likeCount', 'N/A')
            return f"The `likeCount` is '{likecount}'."

    # 6. Author by keyword in postContent
    m = re.search(r'author.*post.*mentioning [\'"]?([\w\s]+)[\'"]?', q)
    if m:
        keyword = m.group(1)
        matched = filter_by_keyword_in_post_content(metadata, keyword)
        if matched:
            author = matched[0].get('author', 'N/A')
            return f"The author of the post is '{author}'."

    # 7. Most common type of post
    if "most common type of post" in q or "most frequent type of post" in q:
        post_type = get_most_common_post_type(metadata)
        if post_type:
            return f"The most common type of post is '{post_type.capitalize()}'."

    # 8. Number of posts made by author
    m = re.search(r'how many posts were made by[\'\"]?([\w\s]+)[\'\"]?', q)
    if m:
        author = m.group(1)
        count = sum(1 for post in metadata if normalize_text(post.get('author', '')) == normalize_text(author))
        return f"'{count}' posts were made by {author} as the author."

    # 9. Average likeCount
    if "average likecount" in q or "average number of likes" in q:
        avg = calculate_average_likecount(metadata)
        if avg is not None:
            return f"The average `likeCount` for all posts is approximately '{round(avg, 2)}'."

    # 10. Details about posts mentioning a keyword
    m = re.search(r'details.*mentions[\'"]?([\w\s]+)[\'"]?', q)
    if m:
        keyword = m.group(1)
        matched = filter_by_keyword_in_post_content(metadata, keyword)
        if matched:
            post = matched[0]
            url_ = post.get('postUrl', 'N/A')
            return (
                f"A post mentioning '{keyword}' has the following details: "
                f"Post Content: '{post.get('postContent', 'N/A')}', "
                f"Author: '{post.get('author', 'N/A')}', "
                f"Post Date: '{post.get('postDate', 'N/A')}', "
                f"Like Count: '{post.get('likeCount', 'N/A')}'.\n"
                f"🔗 Post URL: {url_}"
            )

    # 11. Profile with maximum followers
    if "maximum followers" in q or "most followers" in q or "highest followers" in q:
        def parse_followers(post):
            val = str(post.get('followers', '')).replace('+', '').replace(',', '').strip()
            try:
                return float(re.findall(r'[\d.]+', val)[0])
            except:
                return 0

        top_profile = max(metadata, key=parse_followers, default=None)
        if top_profile:
            name = top_profile.get("name", "N/A")
            title = top_profile.get("description", top_profile.get("title", "N/A"))
            followers = top_profile.get("followers", "N/A")
            profile_url = top_profile.get("profile_url", top_profile.get("profileUrl", "N/A"))
            return (
                f"The person with the most followers is '{name} - {title}' "
                f"with '{followers}' followers.\n\n🔗 Profile URL: {profile_url}"
            )

    # 12. Post with maximum likes
    if "maximum likes" in q or "most likes" in q or "highest likes" in q:
        def parse_likes(post):
            try:
                return float(str(post.get('likeCount', '0')).replace('+', '').replace(',', '').strip())
            except:
                return 0

        liked_post = max(metadata, key=parse_likes, default=None)
        if liked_post:
            content = liked_post.get('postContent', 'N/A')
            author = liked_post.get('author', 'N/A')
            likecount = liked_post.get('likeCount', 'N/A')
            url = liked_post.get('postUrl', 'N/A')
            return (
                f"The post with the most likes has '{likecount}' likes.\n\n"
                f"📝 Post Content: '{content}'\n👤 Author: {author}\n🔗 Post URL: {url}"
            )

    # 13. Post with maximum comments
    if "maximum comments" in q or "most comments" in q or "highest comments" in q:
        def parse_comments(post):
            try:
                return float(str(post.get('commentCount', '0')).replace('+', '').replace(',', '').strip())
            except:
                return 0

        commented_post = max(metadata, key=parse_comments, default=None)
        if commented_post:
            content = commented_post.get('postContent', 'N/A')
            author = commented_post.get('author', 'N/A')
            comments = commented_post.get('commentCount', 'N/A')
            url = commented_post.get('postUrl', 'N/A')
            return (
                f"The post with the most comments has '{comments}' comments.\n\n"
                f"📝 Post Content: '{content}'\n👤 Author: {author}\n🔗 Post URL: {url}"
            )

    # 🔥 Enhanced fallback: quoted keyword
    m = re.search(r'["\']([\w\s]+)["\']', question)
    if m:
        quoted_kw = m.group(1)
        matched = filter_by_keyword_in_post_content(metadata, quoted_kw)
        if matched:
            post = matched[0]
            url_ = post.get('postUrl', 'N/A')
            return (
                f"Here's a post mentioning '{quoted_kw}': {post.get('postContent', 'N/A')}\n"
                f"🔗 Post URL: {url_}"
            )

    # 🧠 Fallback: use any keyword
    tokens = normalize_and_tokenize(q)
    for token in tokens:
        matched = filter_by_keyword_in_post_content(metadata, token)
        if matched:
            post = matched[0]
            url_ = post.get('postUrl', 'N/A')
            return (
                f"Here's a post related to '{token}': {post.get('postContent', 'N/A')}\n"
                f"🔗 Post URL: {url_}"
            )

    return "Sorry, I couldn't find an answer to that question."
