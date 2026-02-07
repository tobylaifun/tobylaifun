#!/usr/bin/env python3
"""
Generate GitHub Profile README based on username and star rankings
"""

import json
import os
import sys
from datetime import datetime
from typing import List, Dict
import urllib.request
import urllib.error


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
        return {
            'login': username,
            'name': 'Toby Lai' if username in ['tobylai-toby', 'tobylaifun'] else username,
            'bio': None,
            'blog': 'https://tobylai.fun' if username in ['tobylai-toby', 'tobylaifun'] else '',
            'location': '',
            'public_repos': 72,
            'followers': 59
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

### 📊 GitHub Profile Views / 访问统计
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
