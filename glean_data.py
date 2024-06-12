import numpy as np
from urllib.request import Request
from urllib.request import urlopen
import re

def lookup(player):
    if player == 'jordan spieth': return '14636'
    if player == 'justin thomas': return '1'
    return 'penis'

def glean_tournament_data():
    # glean tournament archives in datagolf.com
    archive_url = 'https://datagolf.com/raw-data-archive'
    request = Request(url=archive_url, headers={'User-Agent':'Mozilla/5.0'})
    page = urlopen(request)
    html_bytes = page.read()
    html = html_bytes.decode("utf-8")

    # extract tournament data
    archives = []
    years = []
    event_ids = []
    dates = [i.start() for i in re.finditer('\"date\":',html)]
    ids = [i.start() for i in re.finditer('\"event_id\"',html)]
    names = [i.start() for i in re.finditer('\"event_name\"',html)]
    tours = [i.start() for i in re.finditer('\"tour\"',html)]
    for i in range(len(ids)):
        tour = html[tours[i]+9:tours[i]+12]
        if tour == 'pga':
            temp = html[dates[i]+9:dates[i]+9+20]
            date = html[dates[i]+9:dates[i]+9+temp.find('\",')]
            temp = html[ids[i]+12:ids[i]+12+20]
            id = int(html[ids[i]+12:ids[i]+12+temp.find(',')])
            temp = html[names[i]+15:names[i]+15+150]
            name = html[names[i]+15:names[i]+15+temp.find('\",')]
            archives.append([date,name,id])
            date_year = int(date[date.find(', 20')+2:date.find(', 20')+6])
            if date_year not in years: years.append(date_year)
            if id not in event_ids: event_ids.append(id)

    # extract the player results from every tournament on datagolf.com
    player_stats = []
    stat_labels = ['date','tournament_name','tournament_id','course_name','player_name','player_num','pos','r1','r2','r3','r4']
    got_labels = False
    for y in range(len(years)):
        print()
        print('-----------------------' + str(years[y]) + '----------------------')
        print()
        tournaments_gleaned = []
        for e in range(len(event_ids)):
            # get website data as text
            player_url = 'https://datagolf.com/historical-tournament-stats?event_id=' + str(event_ids[e]) + '&year=' + str(years[y])
            request = Request(url=player_url, headers={'User-Agent':'Mozilla/5.0'})
            page = urlopen(request)
            html_bytes = page.read()
            html = html_bytes.decode("utf-8")

            # extract tournament name
            temp = html[html.find('<title>')+7:html.find('<title>')+500]
            tournament = html[html.find('<title>')+7:html.find('title')+7+temp.find(' |')-1]

            if tournament not in tournaments_gleaned:
                print(tournament)
                # extract year
                # year = int(html[html.find('year\" id=\"')+10:html.find('year\" id=\"')+14])
                #print(year)

                # extract course name
                temp = html[html.find('\"course_name')+16:html.find('\"course_name')+200]
                course = html[html.find('\"course_name')+16:html.find('\"course_name')+16+temp.find('\"')]

                # extract scores
                scores_text = html[int(html.find('var reload_data')):int(html.find('\"quick_stats\"'))]
                starts = [i.start() for i in re.finditer('\"player_name\"',scores_text)]
                stops = [i.start() for i in re.finditer('\"total_score\"',scores_text)]
                scores = []
                for i in range(len(starts)):
                    entry = scores_text[starts[i]:stops[i]]
                    score_stats = []
                    start = entry.find(':')
                    stop = entry.find('\",')
                    score_stats.append(entry[start+3:stop])
                    entry = entry[stop+2:]
                    while entry.find(',') != -1:
                        start = entry.find(':')
                        stop = entry.find(',')
                        stat = int(entry[start+2:stop])
                        if stat == -9999: stat = -1
                        score_stats.append(stat)
                        entry = entry[stop+1:]
                    scores.append(score_stats)
                scores = sorted(scores)

                # find indeces of stats in the text
                full_stats_start = int(html.find('\"stat_info\": \"full\"'))
                full_stats_stop = int(html.find('var current_round = '))
                starts = [i.start() if i.start() > full_stats_start and i.start() < full_stats_stop else -1 for i in re.finditer('\": \\[',html)]
                stops = [i.start() if i.start() > full_stats_start and i.start() < full_stats_stop else -1 for i in re.finditer('], \"',html)]
                starts = starts[5:-2]
                stops = stops[4:]

                # extract data
                tournament_stats = []
                for i in range(len(starts)):
                    # extract stat labels
                    if got_labels == False:
                        temp = html[starts[i]-20:starts[i]][::-1]
                        label = html[starts[i]-temp.find('\"'):starts[i]]
                        stat_labels.append(label)
                        if i == len(starts)-1: got_labels = True
                    
                    # extract player ranks
                    tournament_stats.append(html[starts[i]:stops[i]])

                # organize data
                stats = []
                for i in range(len(tournament_stats)):
                    data = tournament_stats[i]
                    rankings = [j.start() for j in re.finditer('\"event\"',data)]
                    players = [j.start() for j in re.finditer('\"player_num\"',data)]
                    stat_pairs = []
                    for j in range(len(rankings)):
                        temp = data[rankings[j]+9:rankings[j]+200]
                        rank = float(data[rankings[j]+9:rankings[j]+9+temp.find(',')])
                        if rank == -9999: rank = -1
                        temp = data[players[j]+14:players[j]+22]
                        player = data[players[j]+15:players[j]+14+temp.find(',')-1]
                        stat_pairs.append([player, rank])
                    stats.append(stat_pairs)
                
                # consolidate rankings for each player
                stats_org = []
                for j in range(len(stats[0])):
                    player_rankings = [stats[0][j][0]]
                    for i in range(len(stats)):
                        player_rankings.append(stats[i][j][1])
                    stats_org.append(player_rankings)
                stats_org = sorted(stats_org)

                # concatenate each player scores and stats into one entry
                for i in range(len(scores)):
                    date = ''
                    id = -1
                    for j in range(len(archives)):
                        if int(archives[j][0][-4:]) == years[y] and (archives[j][1] == tournament or (tournament in archives[j][1] and 'present' in archives[j][1])):
                            date = archives[j][0][:]
                            id = str(archives[j][2])
                            break
                    player_entry = [date,tournament,id,course]
                    for j in range(len(scores[i])):
                        player_entry.append(scores[i][j])
                    if len(stats_org) > 0:
                        for j in range(1,len(stats_org[i])):
                            player_entry.append(stats_org[i][j])
                    player_stats.append(player_entry)
                
                tournaments_gleaned.append(tournament)

    stats_with_labels = player_stats
    player_stats.insert(0,stat_labels) 
    return stats_with_labels

def glean_course_data():
    # get website data as text
    course_url = 'https://datagolf.com/course-table'
    request = Request(url=course_url, headers={'User-Agent':'Mozilla/5.0'})
    page = urlopen(request)
    html_bytes = page.read()
    html = html_bytes.decode("utf-8")

    # extract course info
    starts = [i.start() for i in re.finditer('{\"adj_driving_accuracy\": 0', html)] 
    stops = [i.start()+22 for i in re.finditer('\"yardage_rank\"', html)] 
    course_stats = []
    for i in range(len(starts)):
        if html[starts[i]:stops[i]].find('\"course_name\"') != -1:
            course_stats.append(html[starts[i]:stops[i]])

    # organize course info
    dataset = [[] for i in range(len(course_stats))]
    dataset_labels = []
    for i in range(len(course_stats)):
        stats = course_stats[i]
        quotes = [j.start() for j in re.finditer('\"', stats)]
        ranks = [j.start() for j in re.finditer('\":', stats)]
        entries = []

        if i == 0:
            for j in range(len(quotes)-1):
                if stats[quotes[j]+1:quotes[j+1]].find(' ') == -1:
                    dataset_labels.append(stats[quotes[j]+1:quotes[j+1]])
        for j in range(len(ranks)):
            temp = stats[ranks[j]+3:ranks[j]+150]
            if j < len(ranks)-1: x = 0
            else: x = -1
            entries.append(stats[ranks[j]+3:ranks[j]+3+temp.find(',')+x])
        dataset[i] = entries
    
    dataset_with_labels = [[] for i in range(len(dataset)+1)]
    dataset_with_labels[0] = dataset_labels
    for i in range(1,len(dataset_with_labels)):
        dataset_with_labels[i] = dataset[i-1]
    
    course_idx = dataset_labels.index('course_name')
    dataset_org = []
    for i in range(len(dataset_with_labels)):
        entry_org = []
        entry_org.append(dataset_with_labels[i][course_idx][:])
        for j in range(len(dataset_with_labels[i])):
            if j != course_idx:
                entry_org.append(dataset_with_labels[i][j])
        dataset_org.append(entry_org)

    return dataset_org

if __name__ == "__main__":
    glean_courses = False
    glean_tournaments = True

    if glean_courses:
        course_data = glean_course_data()
        print()
        print('~~~~~~~~~~~~~~~~~Course data gleaned~~~~~~~~~~~~~~~~~~~')
        print()
        # save course stats
        with open('./course_data.txt', 'w') as file:
            for course in course_data:
                for stat in course:
                    file.write(stat + '\t')
                file.write('\n')
    
    if glean_tournaments:
        tournament_data = glean_tournament_data()
        print()
        print('~~~~~~~~~~~~~~~~~Tournament data gleaned~~~~~~~~~~~~~~~~~~~')
        print()
        # save tournament stats
        with open('./tournament_data.txt', 'w') as file:
            for entry in tournament_data:
                for stat in entry:
                    file.write(str(stat) + '\t')
                file.write('\n')