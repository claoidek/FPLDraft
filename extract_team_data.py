import re

def read_file(filename):
    with open(filename, 'r') as fp:
        important_lines = fp.readlines()[500:800] # This range should containt all the data we need
        no_equals = [sub[: -2] for sub in important_lines] # Removes the last character of every line to get rid of inconvenient equals signs
        return(''.join(no_equals))

def extract_data(data):
    players, points = [], []
    score_regex = re.search("Latest Points</h4><div class=3D\"EntryEvent__PrimaryValue-ernz96-3 gcscIr\">(\d+)", data)
    score = (score_regex.group(1))
    players_regex = re.findall("([\w=\d\s]+)</div><div class=3D\"PitchElement__ElementValue-rzo355-3 fKolYJ\">(\d+)",data)
    for match in players_regex:
        if "=" in match[0]:
            unicode_regex = re.findall("=([\d\w]{2})=([\d\w]{2})",match[0])
            for unicode_match in unicode_regex:
                players.append(re.sub("=" + unicode_match[0] + "=" + unicode_match[1],bytes.fromhex(unicode_match[0] + unicode_match[1]).decode(),match[0]))
        else:
            players.append(match[0])
        points.append(match[1])
    return players, points, score

if __name__ == "__main__":
    managers = ["Brian","Caoimhín","Niamh","Seán","Violet"]
    scores = []
    for manager in managers:
        filename = manager + ".mht"
        data = read_file(filename)
        print("\n" + manager)
        players, points, score = extract_data(data)
        scores.append(score)
        for player in players:
            print(player)
        for point in points:
            print(point)

    print("\nScores")
    for score in scores:
        print(score)
