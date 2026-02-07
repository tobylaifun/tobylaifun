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
            'name': username,
            'bio': None,
            'blog': '',
            'location': '',
            'public_repos': 0,
            'followers': 0
        }


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
                'name': 'tobylai-toby',
                'html_url': 'https://github.com/tobylaifun/tobylai-toby',
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
    
    # Filter out forks and sort by stars
    own_repos = [r for r in repos if not r.get('fork', False)]
    sorted_repos = sorted(own_repos, key=lambda x: x.get('stargazers_count', 0), reverse=True)
    
    # Get top repos with stars
    top_repos = [r for r in sorted_repos if r.get('stargazers_count', 0) > 0][:10]
    
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
    if username == "tobylai-toby":
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
    
    # Add dao3.fun if this is tobylai-toby
    if username == "tobylai-toby":
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
        readme += """I'm passionate about building creative and fun things: extensions, CLIs, web tools, LLM apps, and more.  
喜欢做各种有趣的项目，比如扩展、命令行工具、Web 应用、AI App等。

"""
    
    # Add dao3.fun info for tobylai-toby
    if username == "tobylai-toby":
        readme += """I love [dao3.fun](https://dao3.fun), a platform for creating & playing maps!  
也热爱 [dao3.fun 神奇代码岛](https://dao3.fun)，一个属于创作者和玩家的地图平台。

"""
    
    # Add statistics section
    readme += f"""## 📈 GitHub Statistics / GitHub 统计

- **Public Repositories / 公开仓库**: {public_repos}
- **Total Stars / 总星标数**: ⭐ {total_stars}
- **Followers / 关注者**: {followers}

---

"""
    
    # Add top repositories section
    if top_repos:
        readme += """## ⭐ Top Repositories by Stars / 星标排名项目

| Repository | Description | Stars | Language | Updated |
| ---------- | ----------- | ----- | -------- | ------- |
"""
        for repo in top_repos:
            repo_name = repo['name']
            repo_url = repo['html_url']
            description = repo.get('description', 'No description')[:80]
            if len(repo.get('description', '')) > 80:
                description += '...'
            stars = repo.get('stargazers_count', 0)
            language = repo.get('language', 'N/A')
            updated = repo.get('updated_at', '')[:10]
            
            readme += f"| [{repo_name}]({repo_url}) | {description} | ⭐ {stars} | {language} | {updated} |\n"
        
        readme += "\n---\n\n"
    
    # Add featured projects section (keeping the original if tobylai-toby)
    if username == "tobylai-toby":
        readme += """## ✨ Featured Projects / 特色项目

| Project | Description | Main Techs | Status |
| ------- | ----------- | ---------- | ------ |
| [Arenaless](https://github.com/Box3TRC/ArenaLess) | Dao3 Arena TypeScript programming with vscode.dev support<br>Dao3 Arena编辑器 TypeScript 编程，支持 vscode.dev | ![TypeScript](https://img.shields.io/badge/TypeScript-3178c6?logo=typescript&logoColor=white) | Active |
| [Box3Convert](https://github.com/Box3TRC/Box3Convert) | Tools for Dao3/Box3 format & resource conversion<br>Dao3/Box3 资源格式转换小工具(方块/模型/俯视图转化) | ![JavaScript](https://img.shields.io/badge/JavaScript-f7df1e?logo=javascript&logoColor=black) | Active |
| [OnlineObj2Voxel](https://github.com/tobylai-toby/OnlineObj2Voxel) | Online OBJ-to-voxel converter for Dao3/Box3 (JS+WASM)<br>OBJ 模型在线转体素，支持 Dao3/Box3，JS+WASM | ![JavaScript](https://img.shields.io/badge/JavaScript-f7df1e?logo=javascript&logoColor=black) ![WebAssembly](https://img.shields.io/badge/WASM-blueviolet?logo=webassembly&logoColor=white) | Active |
| [Areact](https://github.com/Box3TRC/Areact) | Arena + React: React framework UI for Dao3 (experimental)<br>Dao3 的 React 框架 UI（实验性，TypeScript） | ![TypeScript](https://img.shields.io/badge/TypeScript-3178c6?logo=typescript&logoColor=white) | Experimental |
| [daopy-runtime](https://github.com/tobylai-toby/daopy-runtime) | Run Python on Dao3, API integration (TypeScript/Python)<br>Dao3 上运行 Python 的运行时（Arenaless包含此在线模板） | ![TypeScript](https://img.shields.io/badge/TypeScript-3178c6?logo=typescript&logoColor=white) ![Python](https://img.shields.io/badge/Python-3776ab?logo=python&logoColor=white) | Active |
| [QMCLI](https://github.com/tobylai-toby/QMCLI) | Quick Minecraft Launcher CLI (archived)<br>快速 Minecraft 启动器 CLI（已归档） | ![TypeScript](https://img.shields.io/badge/TypeScript-3178c6?logo=typescript&logoColor=white) | Archived |

---

"""
    
    # Add preferences section
    readme += """## ❤️ What I Like / 偏好

![Deno](https://img.shields.io/badge/Deno-black?logo=deno&logoColor=white)
![Bun](https://img.shields.io/badge/Bun-black?logo=bun&logoColor=white)
![Node.js](https://img.shields.io/badge/Node.js-339933?logo=node.js&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776ab?logo=python&logoColor=white)
"""
    
    if username == "tobylai-toby":
        readme += """[![dao3.fun](https://img.shields.io/badge/dao3.fun-platform-1e90ff)](https://dao3.fun)
"""
    
    readme += """![React](https://img.shields.io/badge/React-61dafb?logo=react&logoColor=black)
![Vue.js](https://img.shields.io/badge/Vue.js-42b883?logo=vue.js&logoColor=white)

喜欢 TypeScript、Node.js、Python，也关注新兴的 Deno/Bun。前端偏爱 React/Vue，业余也折腾 Minecraft、平台开发等。

---

"""
    
    # Add contact section
    readme += """## 📫 Links & Contact / 联系

"""
    
    if blog:
        blog_display = blog.replace('https://', '').replace('http://', '')
        readme += f"- 📝 [Blog {blog_display}]({blog})\n"
    
    if username == "tobylai-toby":
        readme += """- 🤝 [@Box3TRC Organization](https://github.com/Box3TRC)  
- 💬 [dao3.fun](https://dao3.fun)  
"""
    
    readme += """
---

"""
    
    # Add GitHub stats
    readme += f"""## 📊 GitHub Stats

![{name}'s GitHub stats](https://github-readme-stats.vercel.app/api?username={username}&show_icons=true&theme=default)
![Top Langs](https://github-readme-stats.vercel.app/api/top-langs/?username={username}&layout=compact&size_weight=0.5&count_weight=0.5&hide=java)

---

_Thanks for visiting! Feel free to explore my work or connect for collaboration._  
_感谢访问，欢迎交流或一起折腾！_

---

<sub>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')} | Auto-generated by [generate_readme.py](generate_readme.py)</sub>
"""
    
    return readme


def main():
    """Main function"""
    # Get username from command line or environment
    username = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('GITHUB_REPOSITORY_OWNER', 'tobylai-toby')
    
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
