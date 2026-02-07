#!/usr/bin/env python3
"""
Generate GitHub Profile README based on username and star rankings
"""

import glob
import json
import os
import sys
from datetime import datetime
from typing import List, Dict
import urllib.request
import urllib.error


def fetch_repo_stargazers_history(owner: str, repo: str, max_stars: int = 100) -> List[Dict]:
    """Fetch stargazer timestamps for a repository using GitHub API
    
    Returns list of {'starred_at': 'timestamp'} for each star
    Note: Limited to max_stars to avoid rate limiting
    """
    stargazers = []
    page = 1
    per_page = 100
    
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/vnd.github.v3.star+json'  # Get star timestamps
    }
    
    # Add token if available
    github_token = os.environ.get('GITHUB_TOKEN')
    if github_token:
        headers['Authorization'] = f'token {github_token}'
    
    try:
        while len(stargazers) < max_stars:
            url = f"https://api.github.com/repos/{owner}/{repo}/stargazers?page={page}&per_page={per_page}"
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                if not data:
                    break
                
                for item in data:
                    if 'starred_at' in item:
                        stargazers.append({
                            'starred_at': item['starred_at'],
                            'repo': repo
                        })
                
                if len(data) < per_page:
                    break
                    
                page += 1
                
                # Stop if we've collected enough
                if len(stargazers) >= max_stars:
                    break
                    
    except Exception as e:
        print(f"Warning: Could not fetch stargazers for {owner}/{repo}: {e}")
    
    return stargazers


def aggregate_star_history(username: str, repos: List[Dict], max_per_repo: int = 100) -> tuple:
    """Aggregate star history from all repositories
    
    Returns tuple: (history_list, repo_creations)
    - history_list: [{'date': 'YYYY-MM-DD', 'stars': count}] sorted by date
    - repo_creations: {date: [repo_name1, repo_name2, ...]} repos created on that date
    """
    from collections import defaultdict
    
    all_stargazers = []
    repo_creations = defaultdict(list)
    
    # Fetch stargazers for repositories (by star count)
    sorted_repos = sorted(repos, key=lambda x: x.get('stargazers_count', 0), reverse=True)
    
    print(f"Fetching star history for repositories...")
    for repo in sorted_repos:
        repo_name = repo['name']
        star_count = repo.get('stargazers_count', 0)
        created_at = repo.get('created_at', '')[:10]  # Extract YYYY-MM-DD
        
        # Track repo creation date
        if created_at:
            repo_creations[created_at].append(repo_name)
        
        if star_count == 0:
            continue
            
        print(f"  Fetching {repo_name} ({star_count} stars, created {created_at})...")
        stargazers = fetch_repo_stargazers_history(username, repo_name, max_per_repo)
        all_stargazers.extend(stargazers)
        
        missing_stars = star_count - len(stargazers)
        if missing_stars > 0:
            fallback_date = created_at or repo.get('updated_at', '')[:10] or datetime.now().strftime('%Y-%m-%d')
            for _ in range(missing_stars):
                all_stargazers.append({
                    'starred_at': f"{fallback_date}T00:00:00Z",
                    'repo': repo_name
                })
    
    if not all_stargazers:
        print("No star history data available")
        return [], dict(repo_creations)
    
    # Aggregate by date
    daily_stars = defaultdict(int)
    for star in all_stargazers:
        date = star['starred_at'][:10]  # Extract YYYY-MM-DD
        daily_stars[date] += 1
    
    for created_date in repo_creations.keys():
        if created_date not in daily_stars:
            daily_stars[created_date] = 0
    
    # Convert to cumulative sum
    sorted_dates = sorted(daily_stars.keys())
    cumulative = []
    total = 0
    
    for date in sorted_dates:
        total += daily_stars[date]
        cumulative.append({
            'date': date,
            'stars': total
        })
    
    print(f"Generated star history: {len(cumulative)} data points")
    print(f"Repository creations tracked: {len(repo_creations)} dates")
    return cumulative, dict(repo_creations)


def generate_star_trend_svg(history: List[Dict], repo_creations: Dict[str, List[str]], username: str) -> str:
    """Generate SVG chart showing star growth with repo creation markers"""
    if len(history) < 2:
        return ""
    
    # SVG dimensions
    width = 900
    height = 400
    padding_left = 60
    padding_right = 40
    padding_top = 60
    padding_bottom = 80
    chart_width = width - padding_left - padding_right
    chart_height = height - padding_top - padding_bottom
    
    # Get data
    dates = [entry['date'] for entry in history]
    stars = [entry['stars'] for entry in history]
    
    max_stars = max(stars)
    min_stars = 0
    star_range = max_stars if max_stars > 0 else 1
    total_repos_created = sum(len(repos) for repos in repo_creations.values())
    
    # Helper function to convert data to coordinates
    def get_x(index):
        return padding_left + (index / (len(dates) - 1)) * chart_width
    
    def get_y(star_count):
        return padding_top + chart_height - ((star_count - min_stars) / star_range) * chart_height
    
    # Generate path for the star trend line
    points = []
    for i, star_count in enumerate(stars):
        x = get_x(i)
        y = get_y(star_count)
        points.append(f"{x},{y}")
    
    path_data = "M " + " L ".join(points)
    
    # Create SVG
    svg = f'''<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <!-- Background -->
  <rect width="{width}" height="{height}" fill="#ffffff"/>
  
  <!-- Title -->
  <text x="{width//2}" y="30" text-anchor="middle" font-size="18" font-weight="bold" fill="#333">
    ⭐ Total Stars Growth Trend / 总星标增长趋势
  </text>
  
  <!-- Y-axis labels -->
  <text x="{padding_left - 10}" y="{padding_top}" text-anchor="end" font-size="12" fill="#666">{max_stars}</text>
  <text x="{padding_left - 10}" y="{padding_top + chart_height}" text-anchor="end" font-size="12" fill="#666">{min_stars}</text>
  <text x="{padding_left - 10}" y="{padding_top + chart_height//2}" text-anchor="end" font-size="12" fill="#666">{max_stars//2}</text>
  
  <!-- Grid lines -->
  <line x1="{padding_left}" y1="{padding_top}" x2="{padding_left + chart_width}" y2="{padding_top}" stroke="#e0e0e0" stroke-width="1"/>
  <line x1="{padding_left}" y1="{padding_top + chart_height//2}" x2="{padding_left + chart_width}" y2="{padding_top + chart_height//2}" stroke="#e0e0e0" stroke-width="1" stroke-dasharray="5,5"/>
  <line x1="{padding_left}" y1="{padding_top + chart_height}" x2="{padding_left + chart_width}" y2="{padding_top + chart_height}" stroke="#666" stroke-width="2"/>
  
  <!-- Axes -->
  <line x1="{padding_left}" y1="{padding_top}" x2="{padding_left}" y2="{padding_top + chart_height}" stroke="#666" stroke-width="2"/>
  
  <!-- X-axis labels -->
  <text x="{padding_left}" y="{height - padding_bottom + 20}" text-anchor="start" font-size="11" fill="#999">{dates[0]}</text>
  <text x="{padding_left + chart_width}" y="{height - padding_bottom + 20}" text-anchor="end" font-size="11" fill="#999">{dates[-1]}</text>
  
  <!-- Star trend line -->
  <path d="{path_data}" stroke="#4CAF50" stroke-width="3" fill="none"/>
  
  <!-- Regular data points -->
  <g>
'''
    
    label_boxes = []
    label_line_height = 12
    label_padding = 4
    max_label_width = 220
    min_label_width = 80
    # Increased offsets to spread labels further apart and avoid overlaps
    label_position_offsets = (0, 1, -1, 2, -2, 3, -3, 4, -4, 5, -5, 6, -6, 7, -7, 8, -8)

    def boxes_overlap(box_a, box_b):
        """Return True when label boxes (x_min, x_max, y_min, y_max) overlap."""
        return not (box_a[1] < box_b[0] or box_a[0] > box_b[1] or box_a[3] < box_b[2] or box_a[2] > box_b[3])

    # Add data points
    for i, (date, star_count) in enumerate(zip(dates, stars)):
        x = get_x(i)
        y = get_y(star_count)
        
        # Check if this date has repo creations
        if date in repo_creations:
            # Special marker for repo creation dates
            repos = repo_creations[date]
            repo_lines = [f"📦 {repo}" for repo in repos]
            label_lines = repo_lines + [date]
            label_height = label_line_height * len(label_lines)
            max_line_length = max(len(line) for line in label_lines)
            label_width = min(max_label_width, max(min_label_width, max_line_length * 6))
            
            place_right = x < width - (label_width + padding_right)
            label_x = x + 12 if place_right else x - 12
            text_anchor = "start" if place_right else "end"
            x_min = label_x if place_right else label_x - label_width
            x_max = label_x + label_width if place_right else label_x
            
            base_top = y - (label_height / 2)
            min_top = padding_top + label_padding
            max_top = padding_top + chart_height - label_height - label_padding
            base_top = max(min_top, min(base_top, max_top))
            
            # Increased step size to spread labels further apart
            step = label_height + label_padding * 2
            candidate_offsets = label_position_offsets
            label_top = base_top
            label_box = (x_min, x_max, base_top - label_padding, base_top + label_height + label_padding)
            
            # Find the best non-overlapping position
            for offset in candidate_offsets:
                candidate_top = base_top + (offset * step)
                candidate_top = max(min_top, min(candidate_top, max_top))
                candidate_box = (x_min, x_max, candidate_top - label_padding, candidate_top + label_height + label_padding)
                if not any(boxes_overlap(candidate_box, existing) for existing in label_boxes):
                    label_top = candidate_top
                    label_box = candidate_box
                    break
            
            label_boxes.append(label_box)
            repo_names = ', '.join(repos)
            svg += f'''    <!-- Repo creation marker at {date} -->
    <circle cx="{x}" cy="{y}" r="8" fill="#FF5722" stroke="#fff" stroke-width="2"/>
    <title>{date}: Created {repo_names}</title>
'''
            for idx, line in enumerate(label_lines):
                is_repo_line = idx < len(repo_lines)
                font_size = 10 if is_repo_line else 9
                font_color = "#FF5722" if is_repo_line else "#999"
                font_weight = "bold" if is_repo_line else "normal"
                line_y = label_top + label_line_height * (idx + 1)
                svg += f'''    <text x="{label_x}" y="{line_y}" font-size="{font_size}" fill="{font_color}" font-weight="{font_weight}" text-anchor="{text_anchor}">{line}</text>
'''
        else:
            # Regular point (only show every Nth point to avoid clutter)
            if i % max(1, len(dates) // 20) == 0 or i == len(dates) - 1:
                svg += f'''    <circle cx="{x}" cy="{y}" r="3" fill="#4CAF50"/>
'''
    
    svg += '''  </g>
  
  <!-- Legend -->
  <g>
    <circle cx="''' + str(width - 200) + '''" cy="''' + str(height - 40) + '''" r="3" fill="#4CAF50"/>
    <text x="''' + str(width - 190) + '''" y="''' + str(height - 36) + '''" font-size="12" fill="#666">Star count</text>
    
    <circle cx="''' + str(width - 200) + '''" cy="''' + str(height - 20) + '''" r="8" fill="#FF5722" stroke="#fff" stroke-width="2"/>
    <text x="''' + str(width - 190) + '''" y="''' + str(height - 16) + '''" font-size="12" fill="#666">Repo created</text>
  </g>
  
  <!-- Stats -->
  <text x="20" y="''' + str(height - 40) + '''" font-size="11" fill="#666">Total: ''' + str(max_stars) + ''' ⭐</text>
  <text x="20" y="''' + str(height - 25) + '''" font-size="11" fill="#666">Repos created: ''' + str(total_repos_created) + '''</text>
  <text x="20" y="''' + str(height - 10) + '''" font-size="11" fill="#999">Generated: ''' + datetime.now().strftime('%Y-%m-%d') + '''</text>
</svg>'''
    
    return svg




def fetch_github_data(username: str) -> Dict:
    """Fetch user data from GitHub API"""
    url = f"https://api.github.com/users/{username}"
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Add token if available
    github_token = os.environ.get('GITHUB_TOKEN')
    if github_token:
        headers['Authorization'] = f'token {github_token}'
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"Warning: Error fetching user data: {e}")
        print(f"Using fallback data for {username}")
        # Return minimal user data as fallback
        is_toby = username in ['tobylai-toby', 'tobylaifun']
        return {
            'login': username,
            'name': 'Toby Lai' if is_toby else username,
            'bio': 'focusing on interesting things' if is_toby else None,
            'blog': 'https://tobylai.fun' if is_toby else '',
            'location': '',
            'public_repos': 19 if is_toby else 0,
            'followers': 59 if is_toby else 0
        }


def fetch_pinned_repos(username: str) -> List[str]:
    """Fetch pinned repositories for a user using GraphQL API"""
    pinned_repos = []
    
    # Validate username to prevent injection
    if not username or not username.replace('-', '').replace('_', '').isalnum():
        print(f"Warning: Invalid username format: {username}")
        return pinned_repos
    
    query = """
    {
      user(login: "%s") {
        pinnedItems(first: 6, types: REPOSITORY) {
          nodes {
            ... on Repository {
              name
            }
          }
        }
      }
    }
    """ % username
    
    url = 'https://api.github.com/graphql'
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Content-Type': 'application/json',
    }
    
    # Add token if available
    github_token = os.environ.get('GITHUB_TOKEN')
    if github_token:
        headers['Authorization'] = f'Bearer {github_token}'
    
    try:
        data = json.dumps({'query': query}).encode()
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            if 'data' in result and result['data'] and 'user' in result['data']:
                nodes = result['data']['user']['pinnedItems']['nodes']
                pinned_repos = [node['name'] for node in nodes]
                print(f"Found {len(pinned_repos)} pinned repositories")
    except Exception as e:
        print(f"Warning: Could not fetch pinned repos: {e}")
        print("Continuing without pinned repos information")
    
    return pinned_repos


def fetch_user_repos(username: str) -> List[Dict]:
    """Fetch all repositories for a user"""
    repos = []
    page = 1
    per_page = 100
    
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Add token if available
    github_token = os.environ.get('GITHUB_TOKEN')
    if github_token:
        headers['Authorization'] = f'token {github_token}'
    
    while True:
        url = f"https://api.github.com/users/{username}/repos?page={page}&per_page={per_page}&type=owner"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                if not data:
                    break
                repos.extend(data)
                page += 1
        except urllib.error.HTTPError as e:
            print(f"Warning: Error fetching repos: {e}")
            print("Using fallback repository data")
            # Try to load from cache file if it exists
            try:
                if os.path.exists('repos_cache.json'):
                    with open('repos_cache.json', 'r') as f:
                        repos = json.load(f)
                        print(f"Loaded {len(repos)} repos from cache")
            except Exception as cache_err:
                print(f"Could not load cache: {cache_err}")
            break
    
    return repos


def generate_readme(username: str, use_mock: bool = False) -> str:
    """Generate README content based on user data and repositories"""
    
    print(f"Fetching data for user: {username}")
    
    if use_mock:
        # Use mock data for testing
        print("Using mock data for testing")
        user_data = {
            'login': username,
            'name': 'Toby Lai' if username in ['tobylai-toby', 'tobylaifun'] else username,
            'bio': None,
            'blog': 'https://tobylai.fun' if username in ['tobylai-toby', 'tobylaifun'] else '',
            'location': '',
            'public_repos': 15,
            'followers': 10
        }
        repos = [
            {
                'name': 'tobylaifun',
                'html_url': 'https://github.com/tobylaifun/tobylaifun',
                'description': 'My GitHub profile README',
                'stargazers_count': 5,
                'language': 'Python',
                'updated_at': '2026-02-07T00:00:00Z',
                'fork': False
            },
            {
                'name': 'example-project',
                'html_url': 'https://github.com/tobylaifun/example-project',
                'description': 'Example project for demonstration',
                'stargazers_count': 3,
                'language': 'JavaScript',
                'updated_at': '2026-02-06T00:00:00Z',
                'fork': False
            }
        ]
    else:
        user_data = fetch_github_data(username)
        repos = fetch_user_repos(username)
        pinned_repo_names = fetch_pinned_repos(username)
    
    # Filter out forks
    own_repos = [r for r in repos if not r.get('fork', False)]
    
    # Calculate ranking score: pinned repos get +6 stars for sorting
    # but we keep the original star count for display
    if not use_mock:
        pinned_set = set(pinned_repo_names)
        for repo in own_repos:
            repo_name = repo.get('name', '')
            actual_stars = repo.get('stargazers_count', 0)
            # Add ranking_score for sorting (pinned repos get +6 bonus)
            if repo_name in pinned_set:
                repo['ranking_score'] = actual_stars + 6
                repo['is_pinned'] = True
            else:
                repo['ranking_score'] = actual_stars
                repo['is_pinned'] = False
    else:
        # For mock mode, no pinned repos
        for repo in own_repos:
            repo['ranking_score'] = repo.get('stargazers_count', 0)
            repo['is_pinned'] = False
    
    # Sort by ranking_score (which includes pin bonus), not just stars
    sorted_repos = sorted(own_repos, key=lambda x: x.get('ranking_score', 0), reverse=True)
    
    # Get top repos with stars or pinned
    top_repos = [r for r in sorted_repos if r.get('stargazers_count', 0) > 0 or r.get('is_pinned', False)][:10]
    
    # Calculate total stars
    total_stars = sum(r.get('stargazers_count', 0) for r in own_repos)
    
    # Fetch star history from GitHub API (only if not mock mode)
    star_history = []
    repo_creations = {}
    if not use_mock and total_stars > 0:
        print(f"\nFetching star history from GitHub API...")
        star_history, repo_creations = aggregate_star_history(username, own_repos)
    
    # Generate SVG chart if we have history data
    star_chart_svg = ""
    star_chart_filename = ""
    if star_history and len(star_history) >= 2:
        star_chart_svg = generate_star_trend_svg(star_history, repo_creations, username)
        # Save SVG to file
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        star_chart_filename = f'star-history-{timestamp}.svg'
        with open(star_chart_filename, 'w', encoding='utf-8') as f:
            f.write(star_chart_svg)
        print(f"Star trend chart saved to {star_chart_filename}")
        
        # Delete old star history SVG files, keep only the newest one
        all_star_svgs = sorted(glob.glob('star-history-*.svg'))
        if len(all_star_svgs) > 1:
            # Keep the newest (last in sorted list), delete others
            for old_svg in all_star_svgs[:-1]:
                try:
                    os.remove(old_svg)
                    print(f"Removed old star history file: {old_svg}")
                except OSError as e:
                    print(f"Warning: Could not remove {old_svg}: {e}")
    
    # Get user info
    name = user_data.get('name', username)
    bio = user_data.get('bio', '')
    blog = user_data.get('blog', '')
    location = user_data.get('location', '')
    public_repos = user_data.get('public_repos', 0)
    followers = user_data.get('followers', 0)
    
    # Generate README
    readme = f"""# 👋 Hi, I'm {name} (@{username})
# 👋 嗨，我是 {name} (@{username})

<p align="center">
  <a href="https://github.com/{username}">
    <img src="https://img.shields.io/github/followers/{username}?label=Followers&style=social" alt="GitHub Followers" />
  </a>
"""
    
    # Add organization badge if exists
    if username in ["tobylai-toby", "tobylaifun"]:
        readme += """  <a href="https://github.com/Box3TRC">
    <img src="https://img.shields.io/badge/org-Box3TRC-blueviolet?logo=github" alt="Box3TRC Organization" />
  </a>
"""
    
    # Add blog link if exists
    if blog:
        readme += f"""  <a href="{blog}">
    <img src="https://img.shields.io/badge/blog-{blog.replace('https://', '').replace('http://', '')}-orange?logo=google-chrome" alt="Blog" />
  </a>
"""
    
    # Add dao3.fun if this is tobylai-toby or tobylaifun
    if username in ["tobylai-toby", "tobylaifun"]:
        readme += """  <a href="https://dao3.fun">
    <img src="https://img.shields.io/badge/dao3.fun-platform-1e90ff" alt="dao3.fun" />
  </a>
"""
    
    readme += """</p>

---

"""
    
    # Add bio if exists
    if bio:
        readme += f"""{bio}

"""
    else:
        readme += """💻 Full-stack developer passionate about open source and creative coding.

"""
    
    # Add dao3.fun info for tobylai-toby or tobylaifun
    if username in ["tobylai-toby", "tobylaifun"]:
        readme += """I love [dao3.fun](https://dao3.fun), a platform for creating & playing maps!  
也热爱 [dao3.fun 神奇代码岛](https://dao3.fun)，一个属于创作者和玩家的地图平台。

"""
    
    # Add statistics section
    readme += f"""## 📈 GitHub Statistics / GitHub 统计

<div align="center">

| 📊 统计项 | 📈 数值 |
|:---:|:---:|
| 🏆 **Total Stars / 总星标数** | **⭐ {total_stars}** |
| 📦 **Public Repositories / 公开仓库** | **{public_repos}** |
| 👥 **Followers / 关注者** | **{followers}** |

</div>

---

"""
    
    # Add top repositories section
    if top_repos:
        readme += """## ⭐ 推荐项目 / Recommended Projects

| Repository | Description | Stars | Language | Updated |
| ---------- | ----------- | ----- | -------- | ------- |
"""
        for repo in top_repos:
            repo_name = repo['name']
            repo_url = repo['html_url']
            description = repo.get('description') or 'No description'
            if len(description) > 80:
                description = description[:80] + '...'
            stars = repo.get('stargazers_count', 0)
            language = repo.get('language', 'N/A')
            updated = repo.get('updated_at', '')[:10]
            
            readme += f"| [{repo_name}]({repo_url}) | {description} | ⭐ {stars} | {language} | {updated} |\n"
        
        readme += "\n---\n\n"
    
    # Add preferences section
    readme += """## ❤️ What I Like / 偏好

![Deno](https://img.shields.io/badge/Deno-black?logo=deno&logoColor=white)
![Bun](https://img.shields.io/badge/Bun-black?logo=bun&logoColor=white)
![Node.js](https://img.shields.io/badge/Node.js-339933?logo=node.js&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776ab?logo=python&logoColor=white)
"""
    
    if username in ["tobylai-toby", "tobylaifun"]:
        readme += """[![dao3.fun](https://img.shields.io/badge/dao3.fun-platform-1e90ff)](https://dao3.fun)
"""
    
    readme += """![React](https://img.shields.io/badge/React-61dafb?logo=react&logoColor=black)
![Vue.js](https://img.shields.io/badge/Vue.js-42b883?logo=vue.js&logoColor=white)

热爱 TypeScript、Node.js 和 Python 等技术栈，积极探索 Deno、Bun 等新兴运行时。前端方面偏好 React 和 Vue 框架，业余时间也喜欢研究 Minecraft 开发、游戏平台搭建等有趣的项目。

---

"""
    
    # Add contact section
    readme += """## 📫 Links & Contact / 联系

"""
    
    if blog:
        blog_display = blog.replace('https://', '').replace('http://', '')
        readme += f"- 📝 [Blog {blog_display}]({blog})\n"
    
    if username in ["tobylai-toby", "tobylaifun"]:
        readme += """- 🤝 [@Box3TRC Organization](https://github.com/Box3TRC)  
- 💬 [dao3.fun](https://dao3.fun)  
"""
    
    readme += """
---

"""
    
    # Add GitHub stats
    readme += f"""## 📊 GitHub Stats & Analytics / GitHub 数据分析

<div align="center">

### 📈 GitHub Contribution Graph / GitHub 贡献图
![](https://ghchart.rshah.org/{username})

"""
    
    # Add star history chart if data available
    if star_history and len(star_history) >= 2:
        # Display the SVG chart
        first_star = star_history[0]
        last_star = star_history[-1]
        start_date = datetime.strptime(first_star['date'], '%Y-%m-%d')
        end_date = datetime.strptime(last_star['date'], '%Y-%m-%d')
        days_span = (end_date - start_date).days + 1
        num_repos_created = sum(len(repos) for repos in repo_creations.values())
        
        readme += f"""### ⭐ Total Stars Growth Trend / 总星标增长趋势

![Star History Chart]({star_chart_filename})

**Summary / 摘要:**
- 📅 From {first_star['date']} to {last_star['date']} ({days_span} days)
- 📈 Growth: {first_star['stars']} → {last_star['stars']} stars (+{last_star['stars'] - first_star['stars']})
- 💫 Average: ~{(last_star['stars'] - first_star['stars']) / days_span:.2f} stars/day
- 🎯 Repositories created during this period: {num_repos_created}

*Chart shows cumulative stars over time. 🔴 Red dots mark repository creation dates.*

"""
    
    readme += f"""### 📊 GitHub Profile Views / 访问统计
![](https://komarev.com/ghpvc/?username={username}&color=brightgreen&style=flat-square&label=Profile+Views)

</div>

---

_Thanks for visiting! Feel free to explore my projects and reach out for collaboration or discussion._  
_感谢访问！欢迎探索我的项目，也期待与你交流合作。_

---

<sub>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')} | Auto-generated by [generate_readme.py](generate_readme.py)</sub>
"""
    
    return readme


def main():
    """Main function"""
    # Get username from command line or environment
    username = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('GITHUB_REPOSITORY_OWNER', 'tobylaifun')
    
    # Check for mock mode
    use_mock = '--mock' in sys.argv or os.environ.get('USE_MOCK', '').lower() == 'true'
    
    print(f"Generating README for: {username}")
    readme_content = generate_readme(username, use_mock=use_mock)
    
    # Write to README.md
    output_file = 'README.md'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"README.md generated successfully!")
    print(f"Total length: {len(readme_content)} characters")


if __name__ == '__main__':
    main()
