import json
import os
import requests
import argparse
import sys
import urllib3


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

s = requests.Session()
s.verify = False

def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

# get CLI arguments
parser = argparse.ArgumentParser()
parser.add_argument("-u", "--user", help="Username or Organization for parse information.", required=True)
parser.add_argument("-t", "--token", help="Github API token for increase limit 60 req/hour.", required=False, default='')
parser.add_argument("-f", "--getfollowers", help="Also parse commits from followers.", type=str2bool, default=False)
parser.add_argument("-o", "--outputfolder", help="Output folder.", default='output')
parser.add_argument("--getforked", help="Check forked repositories (default: false).", type=str2bool, default=False)
parser.add_argument("--skiprepos", help="Skip repositories parsing (default: false).", type=str2bool, default=False)

args = parser.parse_args()

# check for API token
API_TOKEN = args.token
if API_TOKEN:
    s.headers = {'Authorization': 'token ' + API_TOKEN}

# base variables
name = args.user
parseFollowers = args.getfollowers

# set output folder
outputfolder = args.outputfolder

gathered_info = {}
gusers = []
grepos = []
amembers = []
exclude_users = ['GitHub', 'github', 'github-actions', 'dependabot', 'dependabot-preview', 'dependabot[bot]', 'dependabot-preview[bot]', 'web-flow']
exclude_users_id = [19864447]
exclude_users_emails = ['noreply@github.com']
main_org_id = 0

'''functions'''
def unique_dict(dictionary):
    unique_dicts = set(tuple(d.items()) for d in dictionary.values())
    return [dict(d) for d in unique_dicts]

def unique_list(L):
    return [dict(s) for s in set(frozenset(d.items()) for d in L)]

def get(url):
    r = s.get(url)
    # Check the status code of the response to make sure the request was successful
    if r.status_code == 200:
        return r.json()
    else:
        # If the request was not successful, print an error message
        print(f'An error occurred while trying to get {url}.')
        print(f'Error: {r.status_code}')
        return []

def get_repos(uname):
    return get(f'https://api.github.com/users/{uname}/repos')

def get_followers(uname):
    return get(f'https://api.github.com/users/{uname}/followers')

def gather_user_info(uname, uid, recursive=True):
    if uid in gusers:
        # print(f'User {uname} [{uid}] already processed.')
        return False
    # add user id to list of processed users
    gusers.append(uid)
    print(f'Gathering information for user {uname}.')
    # get user data
    user_data = get(f'https://api.github.com/users/{uname}')
    if 'id' in user_data:
        # fill base user data
        gathered_info[uid] = {
            'id': user_data['id'],
            'org': False,
            'login': user_data['login'],
            'name': user_data['name'],
            'bio': user_data['bio'],
            'email': user_data['email'],
            'company': user_data['company'],
            'avatar_url': user_data['avatar_url'],
            'repos': {}
        }
        # get user repos
        repos_data = get_repos(uname)
        if len(repos_data) > 0:
            for repo in repos_data:
                # fill base repo info
                if repo['fork'] and args.getforked is False:
                    print(f'Repo {repo["name"]} is forked. Skipping.')
                    continue
                gathered_info[uid]['repos'][repo['id']] = {
                    'id': repo['id'],
                    'name': repo['name'],
                    'committers': {},
                    'forked': repo['fork']
                }
                gather_user_info_from_commits(uname, repo["name"], repo["id"], uid, recursive)
    else:
        print(f'User {uname} [{uid}] not found.')
        return False

def gather_user_info_from_commits(uname, rname, rid, bid, recursive=True, ctype='repos'):
    global amembers
    # check if repo is already processed
    if rid in grepos:
        print(f'Repo {rname} [{rid}] already processed.')
        return False
    # add repo id to list of processed repos
    grepos.append(rid)
    print(f'Gathering information for repo {rname}.')
    # get repo commits
    commits_data = get(f'https://api.github.com/{ctype}/{uname}/{rname}/commits')
    if len(commits_data) > 0:
        # Get information about the committers
        # cdata = {}
        adata = [] # authors data array
        for commit in commits_data:
            # commit data collect
            # cdata[commit['sha']] = {
            #     'url': commit['html_url'],
            # }
            # authors collect commit -> author
            if commit['commit']['author']['name'] not in exclude_users:
                adata.append({
                    'name': commit['commit']['author']['name'],
                    'email': commit['commit']['author']['email'],
                })
            # authors collect commit -> committer
            if commit['commit']['author']['name'] not in exclude_users:
                # check github default user format email
                if '@users.noreply.github.com' in commit['commit']['committer']['email']:
                    # convert github default email to id_login list
                    user_id_login = commit['commit']['committer']['email'].split('@')[0].split('+')
                    if len(user_id_login) == 2:
                        # if convert success then try to get info about him through his repositories
                        if (recursive is True) and (commit['author']['login'] not in exclude_users):
                            gather_user_info(user_id_login[1], user_id_login[0], recursive=False)
                adata.append({
                    'name': commit['commit']['committer']['name'],
                    'email': commit['commit']['committer']['email'],
                })
            # author collect
            if commit['author'] is not None and commit['author']['type'] == 'User':
                # if author is User then try to get info about him through his repositories
                if (recursive is True) and (commit['author']['login'] not in exclude_users):
                    gather_user_info(commit['author']['login'], commit['author']['id'], recursive=False)
                adata.append({
                    'name': commit['author']['login'],
                    'id': commit['author']['id'],
                })
            # committer collect
            if (commit['committer'] is not None) and (commit['committer']['login'] not in exclude_users):
                # if author is User then try to get info about him through his repositories
                if (recursive is True) and (commit['committer']['login'] not in exclude_users):
                    gather_user_info(commit['committer']['login'], commit['committer']['id'], recursive=False)
                adata.append({
                    'name': commit['committer']['login'],
                    'id': commit['committer']['id'],
                })
        # unique authors for the repo
        committers = unique_list(adata)
        # add committers info into overall data
        amembers += committers
        gathered_info[bid]['repos'][rid].update({
            'committers': committers
        })

def gather_users_from_followers(n):
    followers = get_followers(n)
    for f in followers:
        gather_user_info(f["login"], f["id"], recursive=False)


'''/functions'''

# check limits
limits = get('https://api.github.com/rate_limit')
print(f'You have {limits["resources"]["core"]["remaining"]} API requests left.')

# get base information about specified user/org
print(f'Gathering information for user/org {name}')
base_data = get(f'https://api.github.com/users/{name}')
if 'id' in base_data:
    # add id to list of processed users
    if(base_data['type'] == 'Organization'):
        gusers.append(base_data['id'])
        print(f'{name} is organization.')
        # fill base org data
        gathered_info[base_data['id']] = {
            'id': base_data['id'],
            'org': True,
            'login': base_data['login'],
            'name': base_data['name'],
            'bio': base_data['bio'],
            'email': base_data['email'],
            'company': base_data['company'],
            'avatar_url': base_data['avatar_url'],
            'repos': {},
            'members': [],
            'followers': []
        }
        if args.skiprepos is False:
            # get all repos
            repos_data = get_repos(name)
            if len(repos_data) > 0:
                # get information about each repo
                for repo in repos_data:
                    if repo['fork'] and args.getforked is False:
                        print(f'Repo {repo["name"]} is forked. Skipping.')
                        continue
                    # fill base repo info
                    gathered_info[base_data['id']]['repos'][repo['id']] = {
                        'id': repo['id'],
                        'name': repo['name'],
                        'committers': {},
                        'forked': repo['fork']
                    }
                    # get information about committers
                    gather_user_info_from_commits(name, repo["name"], repo["id"], base_data['id'])
        # try to get members of organization
        members_data = get(f'https://api.github.com/orgs/{name}/members')
        if len(members_data) > 0:
            print(f'Found {len(members_data)} members for organization {name}. Gathering ...')
            for member in members_data:
                # save info about member
                gathered_info[base_data['id']]['members'].append({
                    'id': member['id'],
                    'login': member['login'],
                })
                # get user repos
                print(f"Gathering member {member['login']}'s repos ...")
                gather_user_info(member['login'], member['id'], recursive=False)
        if parseFollowers:
            followers_data = get_followers(name)
            if len(followers_data) > 0:
                print(f'Found {len(followers_data)} followers for organization {name}. Gathering ...')
                for follower in followers_data:
                    # save info about follower
                    gathered_info[base_data['id']]['followers'].append({
                        'id': follower['id'],
                        'login': follower['login'],
                    })
                    # get user repos
                    print(f"Gathering follower {follower['login']}'s repos ...")
                    gather_user_info(follower["login"], follower["id"], recursive=False)

    elif(base_data["type"] == "User"):
        gather_user_info(name, base_data['id'], recursive=False)
        print(f'{name} is user. Gathering repos and try to find committers ...')
        # get followers
        if parseFollowers:
            print(f'Gathering information from {name}\'s followers.')
            gather_users_from_followers(name)

    # save data
    if outputfolder:
        out_folder = outputfolder
    else:
        out_folder = 'output'
    os.makedirs(out_folder, exist_ok=True)
    with open(os.path.join(out_folder, f'{name}.json'), 'w') as f:
        json.dump(gathered_info, f, indent=2)
    with open(os.path.join(out_folder, f'{name}_members.json'), 'w') as f:
        json.dump(unique_list(amembers), f, indent=2)
    print('Execution completed. Exiting ...')
    sys.exit(0)
else:
    print('Nothing found. Exiting ...')
    sys.exit(0)