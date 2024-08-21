#!/opt/homebrew/bin/bash

. .venv/bin/activate

gameweek=$1

declare -A managers=( ["Caoimhín"]="423" ["Niamh"]="821" ["Violet"]="2254" ["Seán"]="267818" ["Brian"]="277625")

echo "Downloading mhtml files for game week $gameweek"
for manager in "${!managers[@]}"; do
    rm -f "$manager.mhtml"
    url="https://draft.premierleague.com/entry/${managers[$manager]}/event/$gameweek"
    echo -e "\tDownloading $manager.mhtml"
    ./single-file $url "$manager.mhtml"
    echo -e "\tDone"
    echo -e "\tReducing size of $manager.mhtml"
    grep cHYlGH "$manager.mhtml" > temp.mhtml
    sed 's/^.*\(Final Points<.*\)/\1/' temp.mhtml > "$manager.mhtml"
    sed 's/^\(.*cHYlGH">[-[:digit:]]*<.\).*/\1/' "$manager.mhtml" > temp.mhtml
    mv temp.mhtml "$manager.mhtml"
    echo -e "\tDone"
done
echo "Done"

echo "Processing scores and squads"
python3 process_FPL_data.py $gameweek
echo "Done"
echo "Success!"
