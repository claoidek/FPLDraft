#!/opt/homebrew/bin/bash

gameweek=$1

declare -A managers=( ["Caoimhín"]="423" ["Niamh"]="821" ["Violet"]="2254" ["Seán"]="267818" ["Brian"]="277625")

for manager in "${!managers[@]}"; do
    rm -f "$manager.mhtml"
    url="https://draft.premierleague.com/entry/${managers[$manager]}/event/$gameweek"
    ./single-file $url "$manager.mhtml"
done

python3 extract_team_data.py
python3 set_and_forget.py $gameweek
