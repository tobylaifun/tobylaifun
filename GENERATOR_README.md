# GitHub Profile README Generator

This repository contains a Python script that automatically generates a GitHub profile README based on your username and repository star rankings.

## Features

- 📊 Fetches real-time GitHub statistics (repositories, stars, followers)
- ⭐ Lists your top repositories with intelligent ranking (pinned repos count as +6 stars)
- 📌 Fetches pinned repositories and merges them into recommendations
- 🤖 Automatic daily updates via GitHub Actions
- 🌐 Bilingual support (English/Chinese)
- 🎨 Beautiful badges and formatting
- 📈 GitHub stats visualizations

## How it Works

The `generate_readme.py` script:
1. Fetches user data from the GitHub API
2. Retrieves all user repositories
3. Fetches pinned repositories via GraphQL API
4. Filters out forks and ranks by combined pin+star score
   - Pinned repositories get +6 stars bonus for ranking
   - Display still shows actual star count
5. Generates a formatted README with:
   - User statistics (repos, stars, followers)
   - Top repositories table ranked by pin+star score
   - Featured projects section
   - Technology preferences
   - Contact links
   - GitHub stats cards

## Usage

### Manual Generation

```bash
# Generate README for a specific user
python3 generate_readme.py <username>

# Test with mock data (useful when API rate-limited)
python3 generate_readme.py <username> --mock
```

### Automatic Updates

The GitHub Actions workflow (`.github/workflows/update-readme.yml`) automatically:
- Runs daily at 00:00 UTC
- Can be triggered manually via workflow_dispatch
- Runs on push to main branch
- Commits and pushes changes if README was updated

## Setup

1. Fork this repository
2. Ensure the workflow has write permissions:
   - Go to Settings > Actions > General
   - Under "Workflow permissions", select "Read and write permissions"
3. The workflow will automatically run and update your README

## Requirements

- Python 3.x (uses only standard library)
- GitHub account
- GitHub token (automatically provided by GitHub Actions)

## Customization

Edit `generate_readme.py` to customize:
- README template and sections
- Which repositories to feature
- Badge styles and colors
- Language preferences
- Stats formatting

## Example Output

The generated README includes:
- Header with name and username
- Badge links (followers, organization, blog, etc.)
- Statistics section with total stars and repository count
- Top repositories table sorted by stars
- Featured projects showcase
- Technology preferences
- Contact information
- GitHub stats visualizations
- Auto-update timestamp

## License

Feel free to use this script for your own profile README!
