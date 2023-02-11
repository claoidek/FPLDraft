import requests, json
import pandas as pd
from pprint import pprint

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
        draft_teams[manager]["subs"][outfield_sub]={"name":player,"position":position,"id":id_num}
    else:
        draft_teams[manager][position][player]=id_num

if __name__ == "__main__":
    pd.set_option('display.max_rows', None)
    #base_url = 'https://fantasy.premierleague.com/api/' 
    #r = requests.get(base_url+'bootstrap-static/').json() 
    #players = pd.json_normalize(r['elements'])
    #teams = pd.json_normalize(r['teams'])
    #positions = pd.json_normalize(r['element_types'])
    #df = pd.merge(
    #    left=players,
    #    right=teams,
    #    left_on='team',
    #    right_on='id'
    #)
    #df = df.merge(
    #    positions,
    #    left_on='element_type',
    #    right_on='id'
    #)
    #df = df.rename(
    #    columns={'name':'team_name', 'singular_name':'position_name'}
    #)
    #print(df[['first_name', 'second_name', 'team_name', 'position_name']].loc[df['web_name'] == 'Dalot'])

    draft_teams = construct_draft_teams()
    print(draft_teams["Brian"]["subs"][3])
