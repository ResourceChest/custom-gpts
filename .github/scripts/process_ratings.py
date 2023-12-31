import os
import re
from github import Github, Auth

# Initialize GitHub API client
auth = Auth.Token(os.environ['MODIFY_TOKEN'])
g = Github(auth=auth)

# Function to parse current ratings from README.md
def parse_readme_for_ratings(readme_content):
    ratings = {}
    lines = readme_content.splitlines()
    header = lines[0]
    data_lines = lines[19:]
    for line in data_lines:
        if '|' in line and line.startswith('|'):
            parts = line.split('|')
            if len(parts) >= 6:  # Considering table structure
                gpt_id = parts[1].strip()
                current_rating = parts[5].strip()  # Ratings column
                ratings[gpt_id] = int(current_rating.replace('+', ''))
    return ratings

# Function to update ratings based on issues
def update_ratings_from_issues(repo, ratings):
    for issue in repo.get_issues(state='open'):
        rating_changed = False
        if 'rating-up' in [label.name for label in issue.labels]:
            gpt_id = issue.title.split('[')[-1].split(']')[0]
            ratings[gpt_id] = ratings.get(gpt_id, 0) + 1
            rating_changed = True
        elif 'rating-down' in [label.name for label in issue.labels]:
            gpt_id = issue.title.split('[')[-1].split(']')[0]
            ratings[gpt_id] = ratings.get(gpt_id, 0) - 1
            rating_changed = True

        # Close the issue if the rating was changed
        if rating_changed:
            issue.edit(state='closed')
    
    return ratings

# Function to update README.md with new ratings
def update_readme_with_ratings(readme_content, ratings):
    new_readme_lines = []
    for line in readme_content.splitlines():
        if '|' in line and line.startswith('|'):
            parts = line.split('|')
            if len(parts) >= 6:  # Considering table structure
                gpt_id = parts[1].strip()
                if gpt_id in ratings:
                    new_rating = f'{ratings[gpt_id]}'
                    parts[5] = f' {new_rating} '  # Update rating
                    new_line = '|'.join(parts)
                    new_readme_lines.append(new_line)
                else:
                    new_readme_lines.append(line)
            else:
                new_readme_lines.append(line)
        else:
            new_readme_lines.append(line)
    return '\n'.join(new_readme_lines)

def main():
    repo = g.get_repo('ResourceChest/custom-gpts')
    readme = repo.get_contents('README.md')
    current_readme_content = readme.decoded_content.decode('utf-8')

    # Parse current ratings
    ratings = parse_readme_for_ratings(current_readme_content)

    # Update ratings from issues
    updated_ratings = update_ratings_from_issues(repo, ratings)

    # Update README with new ratings
    new_readme_content = update_readme_with_ratings(current_readme_content, updated_ratings)
    
    # Push changes to GitHub
    if new_readme_content != current_readme_content:
        repo.update_file('README.md', 'Update GPT ratings', new_readme_content, readme.sha)

if __name__ == '__main__':
    main()
