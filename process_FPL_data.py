import requests, json
import pandas as pd
import csv
import sys
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from openpyxl.utils import get_column_letter

managers = ["Brian","Caoimhín","Niamh","Seán"]
manager_ids = {"Brian":"209940","Caoimhín":"2921","Niamh":"3006","Seán":"214689"}
league_id = '1140'
saf_file="set_and_forget_2627.csv"
draft_file="draft2627.csv"
client_file="client_key.json"
spreadsheet="FPL Draft Stats 2026_27"

def construct_saf_teams():
    saf_teams = {}
    for manager in managers:
        add_saf_team(saf_teams,manager)
    return saf_teams

def add_saf_team(saf_teams,name):
    saf_teams.update({name:{"start_gkp":{},
                              "sub_gkp":{},
                              "def":{},
                              "mid":{},
                              "fwd":{},
                              "subs":{1:{},
                                      2:{},
                                      3:{}}
                              }})


def add_player(saf_teams,manager,position,player,id_num,outfield_sub):
    if(outfield_sub!=0):
        saf_teams[manager]["subs"][outfield_sub]={"name":player,"position":position,"id":id_num,"score":0,"minutes":0}
    else:
        saf_teams[manager][position][player]={}
        saf_teams[manager][position][player]["id"]=id_num
        saf_teams[manager][position][player]["score"]=0
        saf_teams[manager][position][player]["minutes"]=0

def read_player_csv(filename):
    with open(filename, newline='') as f:
        reader = csv.reader(f)
        player_data = list(reader)
    return player_data

def get_player_data():
    r = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/').json() 
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
    #print(df[['first_name', 'second_name', 'team_name', 'position_name','id_x']].loc[df['web_name'] == 'Haaland'])
    return df
   
def get_gameweek_history(player_id):
    r = requests.get('https://fantasy.premierleague.com/api/element-summary/' + str(player_id) + '/').json()
    player_df = pd.json_normalize(r['history'])
    return player_df

def add_gameweek_data(saf_teams,gameweek):
    for manager in managers:
        for position in ["start_gkp","sub_gkp","def","mid","fwd","subs"]:
            for player in saf_teams[manager][position]:
                player_gameweek_history = get_gameweek_history(saf_teams[manager][position][player]["id"])
                saf_teams[manager][position][player]["score"] = player_gameweek_history.loc[player_gameweek_history['round'] == gameweek, 'total_points'].sum()
                saf_teams[manager][position][player]["minutes"] = player_gameweek_history.loc[player_gameweek_history['round'] == gameweek, 'minutes'].sum()

def get_score(team):
    starting_positions = ["def","mid","fwd","start_gkp"]
    positions = ["start_gkp","sub_gkp","def","mid","fwd","subs"]
    min_formation = [3,2,1]
    score = get_initial_score(team)
    formation = get_formation(team)
    num_subs = 0
    for position in starting_positions:
        for player in team[position]:
            if team[position][player]["minutes"] == 0:
                if position == "start_gkp":
                    for player in team["sub_gkp"]:
                        score = score + team["sub_gkp"][player]["score"]
                else:
                    formation[starting_positions.index(position)] = formation[starting_positions.index(position)]-1
                    num_subs = num_subs + 1

    subs_required = [0,0,0]
    for index, position in enumerate(subs_required):
        if min_formation[index] > formation[index]:
            subs_required[index] = min_formation[index] - formation[index]

    while num_subs > 0:
        sub_not_made = True
        if sum(subs_required) > 0:
            for sub in range(1,4):
                if team["subs"][sub]["minutes"] > 0 and subs_required[starting_positions.index(team["subs"][sub]["position"])] > 0:
                    score = score + team["subs"][sub]["score"]
                    num_subs = num_subs - 1
                    team["subs"][sub]["minutes"] = 0
                    subs_required[starting_positions.index(team["subs"][sub]["position"])] = subs_required[starting_positions.index(team["subs"][sub]["position"])] - 1
                    sub_not_made = False
                    break
        else:
            for sub in range(1,4):
                if team["subs"][sub]["minutes"] > 0:
                    score = score + team["subs"][sub]["score"]
                    num_subs = num_subs - 1
                    team["subs"][sub]["minutes"] = 0
                    sub_not_made = False
                    break
        if sub_not_made:
            break

    return int(score)
    

def get_initial_score(team):
    starting_positions = ["start_gkp","def","mid","fwd"]
    initial_score = 0
    for position in starting_positions:
        for player in team[position]:
            initial_score = initial_score + team[position][player]["score"]
    return initial_score

def get_formation(team):
    formation = [len(team["def"]),len(team["mid"]),len(team["fwd"])]
    return formation

def get_standard_data(manager_id, player_data):
    ids, positions, points = [], [], []
    r = requests.get('https://draft.premierleague.com/api/entry/'+manager_id+'/event/'+str(gameweek)).json()
    team = r["picks"].copy()
    for player in team:
        player_gameweek_history = get_gameweek_history(str(player["element"]))
        ids.append(player["element"])
        positions.append(player_data[['position_name']].loc[player_data['id_x'] == player["element"]].values[0][0])
        points.append(player_gameweek_history[['total_points']].loc[player_gameweek_history['round'] == gameweek].values[0][0].item())
    score = sum(points[:11])
    return ids, positions, points, score

def write_squad_to_spreadsheet(client,gameweek,manager,ids,positions,points):
    sheet = client.open(spreadsheet).worksheet("RawSquadData")
    manager_index = managers.index(manager)
    row = 2+manager_index*17
    column = 2+(gameweek-1)*3
    cell_string=get_column_letter(column)+str(row)+":"+get_column_letter(column)+str(row+14)
    sheet.update(values=list(map(list, zip(*[ids]))),range_name=cell_string)
    cell_string=get_column_letter(column+1)+str(row)+":"+get_column_letter(column+1)+str(row+14)
    sheet.update(values=list(map(list, zip(*[positions]))),range_name=cell_string)
    cell_string=get_column_letter(column+2)+str(row)+":"+get_column_letter(column+2)+str(row+14)
    sheet.update(values=list(map(list, zip(*[points]))),range_name=cell_string)
    return

def write_scores_to_spreadsheet(client,gameweek,scores,sheetname):
    sheet = client.open(spreadsheet).worksheet(sheetname)
    row = gameweek+1
    if len(managers)%2 == 0:
        column = 2
    else:
        column = 3
    cell_string=get_column_letter(column)+str(row)+":"+get_column_letter(column+len(managers)-1)+str(row)
    sheet.update(values=[scores],range_name=cell_string)
    return

def authorise_credentials():
    scope = [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/drive.file'
        ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(client_file,scope)
    client = gspread.authorize(creds)
    return client

def process_standard(gameweek,client):
    player_data = get_player_data()
    standard_scores = []
    for manager in manager_ids:
        print("\t\tFetching data for " + manager)
        ids, positions, points, score = get_standard_data(manager_ids[manager],player_data)
        print("\t\tDone")
        standard_scores.append(score)
        print("\t\tWriting " + manager + "'s squad to spreadsheet")
        write_squad_to_spreadsheet(client,gameweek,manager,ids,positions,points)
        print("\t\tDone")
    print("\t\tWriting standard scores to spreadsheet")
    write_scores_to_spreadsheet(client,gameweek,standard_scores,"Scores")
    print("\t\tDone")
    return

def process_saf(gameweek,client):
    saf_scores = []
    saf_teams = construct_saf_teams()
    print("\t\tReading Set-And-Forget teams from file")
    player_data = read_player_csv(saf_file)
    print("\t\tDone")
    print("\t\tAdding players to data structure")
    for player in player_data:
        add_player(saf_teams,player[0],player[1],player[2],int(player[3]),int(player[4]))
    print("\t\tDone")
    print("\t\tGetting players' data for game week " + str(gameweek))
    add_gameweek_data(saf_teams,gameweek)
    print("\t\tDone")
    for manager in managers:
        saf_scores.append(get_score(saf_teams[manager]))
    print("\t\tWriting scores to spreadsheet")
    write_scores_to_spreadsheet(client,gameweek,saf_scores,"SAFScores")
    print("\t\tDone")
    return

def process_draft_scores():
    draft_scores = []
    with open(draft_file,'r') as file:
        players = [i.strip('\n') for i in file.readlines()]
    for player in players:
        r = requests.get('https://fantasy.premierleague.com/api/element-summary/'+player).json()
        draft_scores.append(r["history"][0]["total_points"])
    sheet = client.open(spreadsheet).worksheet("Draft")
    row = 1
    column = 2
    cell_string=get_column_letter(column)+str(row)+":"+get_column_letter(column)+str(row+len(managers)*15)
    sheet.update(values=list(map(list, zip(*[draft_scores]))),range_name=cell_string)
    return

if __name__ == "__main__":
    gameweek = int(sys.argv[1])

    print("Processing scores and squads")
    print("\tAuthorising credentials")
    client = authorise_credentials()
    print("\tDone")
    print("\tProcessing draft scores")
    process_draft_scores()
    print("\tDone")
    print("\tProcessing standard scores and squads")
    process_standard(gameweek,client)
    print("\tDone")
    print("\tProcessing Set-And-Forget scores")
    process_saf(gameweek,client)
    print("\tDone")
    print("Done")
    print("Success!")
