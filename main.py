import requests, json
import pandas as pd
import csv

def construct_draft_teams():
    draft_teams = {}
    for manager in ["Brian","Caoimhín","Niamh","Seán","Violet"]:
        add_draft_team(draft_teams,manager)
    return draft_teams

def add_draft_team(draft_teams,name):
    draft_teams.update({name:{"start_gkp":{},
                              "sub_gkp":{},
                              "def":{},
                              "mid":{},
                              "fwd":{},
                              "subs":{1:{},
                                      2:{},
                                      3:{}}
                              }})


def add_player(draft_teams,manager,position,player,id_num,outfield_sub):
    if(outfield_sub!=0):
        draft_teams[manager]["subs"][outfield_sub]={"name":player,"position":position,"id":id_num,"score":0,"minutes":0}
    else:
        draft_teams[manager][position][player]=id_num
        draft_teams[manager][position]["score"]=0
        draft_teams[manager][position]["minutes"]=0

def read_player_csv(filename):
    with open(filename, newline='') as f:
        reader = csv.reader(f)
        player_data = list(reader)
    return player_data

def get_player_data():
    base_url = 'https://fantasy.premierleague.com/api/' 
    r = requests.get(base_url+'bootstrap-static/').json() 
    players = pd.json_normalize(r['elements'])
    teams = pd.json_normalize(r['teams'])
    positions = pd.json_normalize(r['element_types'])
    df = pd.merge(
        left=players,
        right=teams,
        left_on='team',
        right_on='id'
    )
    df = df.merge(
        positions,
        left_on='element_type',
        right_on='id'
    )
    df = df.rename(
        columns={'name':'team_name', 'singular_name':'position_name'}
    )
    #print(df[['first_name', 'second_name', 'team_name', 'position_name','id_x']].loc[df['web_name'] == 'Dalot'])
    return df
   
def get_gameweek_history(player_id):
    base_url = 'https://fantasy.premierleague.com/api/' 
    r = requests.get(base_url + 'element-summary/' + str(player_id) + '/').json()
    player_df = pd.json_normalize(r['history'])
    return player_df

if __name__ == "__main__":
    draft_teams = construct_draft_teams()
    player_data = read_player_csv("drafted_players_2223.csv")
    for player in player_data:
        add_player(draft_teams,player[0],player[1],player[2],int(player[3]),int(player[4]))
    test = get_gameweek_history(478)
    print(test[['round','minutes','total_points']])
