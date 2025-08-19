#!/opt/homebrew/bin/bash

. .venv/bin/activate

gameweek=$1

declare -A managers=( ["Caoimhín"]="326135" ["Niamh"]="358629" ["Seán"]="360894" ["Violet"]="384238" ["Brian"]="405535")

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
