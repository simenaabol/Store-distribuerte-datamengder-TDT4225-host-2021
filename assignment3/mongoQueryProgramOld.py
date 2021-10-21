from datetime import date, datetime
from pprint import pprint

from bson import SON
from haversine import haversine

from DbConnector import DbConnector


class MongoQueryProgram:

    def __init__(self):
        self.connection = DbConnector()
        self.client = self.connection.client
        self.db = self.connection.db

    # How many users, activities and trackpoints are there in the dataset (after it is inserted into the database).
    def query1(self):
        queries = [""]
        print('\n\nSolution to query 1:\n')
        collections = ["User", "Activity", "TrackPoint"]
        for collection in collections:
            docs = self.db[collection].count_documents({})
            print(collection, ':', docs)

    # Find the average, minimum and maximum number of activities per user.
    def query2(self):
        print('\n\nSolution to query 2:\n')
        commands = ['$max', '$min', '$avg']
        for command in commands:
            docs = self.db['User'].aggregate([
                {
                    '$group': {
                        '_id': 0,
                        'command': {command: {'$size': '$activities_ids'}}
                    }
                }
            ])
            print(command, ' number of activities:')
            pprint(list(docs))

    # Find the top 10 users with the highest number of activities.
    def query3(self):
        print('\n\nSolution to query 3:\n')
        docs = self.db['User'].aggregate([
            {
                '$project': {
                    '_id': '$_id',
                    'activities': {'$size': '$activities_ids'}
                }
            },
            {
                '$sort': {'activities': -1}
            },
            {
                '$limit': 10
            }
        ])
        print('Top ten users:')
        pprint(list(docs))

    # Find the number of users that have started the activity in one day and ended
    # the activity the next day.
    def query4(self):
        print('\n\nSolution to query 4:\n')

        tp_list = self.db['Activity'].aggregate([
            {'$match': {
                '$and': [
                    {'user_id': '112'},
                    {'transportation_mode': 'walk'},
                    {'$expr': {'$and': [{'$year': '$end_date_time'}, '2008']}}
                ]
            }
            },
            {'$lookup': {
                'from': 'TrackPoint',
                'localField': "_id",
                'foreignField': "activity_id",
                'as': 'tp'
            }
            },
            {'$project': {
                'lat': '$tp.lat',
                'lon': '$tp.lon',
            }}
        ])

    # Find activities that are registered multiple times. You should find the query even if you get zero results.
    def query5(self):
        print('\n\nSolution to query 5:\n')
        result = self.db["Activity"].aggregate(
            [
                {
                    "$group": {
                        "_id": {
                            "transportation_mode": "$transportation_mode",
                            "end_date_time": "$end_date_time",
                            "user_id": "$user_id",
                            "start_date_time": "$start_date_time"
                        },
                        "COUNT(*)": {
                            "$sum": 1
                        }
                    }
                },
                {
                    "$project": {
                        "user_id": "$_id.user_id",
                        "transportation_mode": "$_id.transportation_mode",
                        "start_date_time": "$_id.start_date_time",
                        "end_date_time": "$_id.end_date_time",
                        "COUNT(*)": "$COUNT(*)",
                        "_id": 0
                    }
                },
                {
                    "$match": {
                        "COUNT(*)": {
                            "$gt": 1
                        }
                    }
                }
            ]
        );
        pprint(list(result))

    # An infected person has been at position (lat, lon) (39.97548, 116.33031) at
    # time ‘2008-08-24 15:38:00’. Find the user_id(s) which have been close to this
    # person in time and space (pandemic tracking).
    # Close is defined as the same minute (60 seconds) and space (100 meters).
    # (This is a simplification of the “unsolvable” problem given i exercise 2).
    def query6(self):
        print('\n\nSolution to query 6:\n')
        result = self.db["Activity"].aggregate(
            [
                { '$lookup': {
                    'from': 'TrackPoint',
                    'localField': "_id",
                    'foreignField': "activity_id",
                    'as': 'trackPoint'
                }  
                },
                { '$project': {
                    'user_id': '$user_id',
                    'lat': '$trackPoint.lat',
                    'lon': '$trackPoint.lon',
                    'date_time': '$trackPoint.date_time'
                }
                },
                {'$limit': 1
                }
            ])

        tp_list = list(result)
        close_users = []

        infected_person_pos = (39.97548, 116.33031)
        infected_person_time = datetime.strptime("2008-08-24 15:38:00", '%Y-%m-%d %H:%M:%S')


        #print(list(result)[0])

        #first = list(result)[0]

        #print(first['lat'][0])



        #pprint(list(result))

    # Find all users that have never taken a taxi.
    def query7(self):
        print('\n\nSolution to query 7:\n')
        result = self.db["Activity"].aggregate(
            [
                {
                    u"$match": {
                        u"transportation_mode": u"taxi"
                    }
                },
                {
                    u"$project": {
                        u"user_id": u"$user_id",
                        u"_id": 0
                    }
                },
                {
                    u"$group": {
                        u"_id": None,
                        u"distinct": {
                            u"$addToSet": u"$$ROOT"
                        }
                    }
                },
                {
                    u"$unwind": {
                        u"path": u"$distinct",
                        u"preserveNullAndEmptyArrays": False
                    }
                },
                {
                    u"$replaceRoot": {
                        u"newRoot": u"$distinct"
                    }
                }
            ])
        pprint(list(result))
        # Her har jeg bare funnet de som HAR tatt taxi

    # Find all types of transportation modes and count how many distinct users that
    # have used the different transportation modes. Do not count the rows where the
    # transportation mode is null.
    def query8(self):
        print('\n\nSolution to query 8:\n')
        result = self.db["Activity"].aggregate(
            [
                {
                    "$group": {
                        "_id": {
                            "transportation_mode": "$transportation_mode",
                        },
                        "users": {
                            "$sum": 1
                        }
                    }
                },
                {
                    "$sort": {"users": -1}
                },
                {
                    "$project": {
                        "TransportationMode": "$_id.transportation_mode",
                        "NumberOfUsers": "$users",
                        "NumberOfDistinctUsers": "$_id.NumberOfDistinctUsers",
                        "_id": 0
                    }
                },
            ])
        pprint(list(result))
        # Her mangler jeg å fjerne None og å fjerne duplikate users (distinct...)

    # a) Find the year and month with the most activities.
    def query9(self):
        print('\n\nSolution to query 9a:\n')
        result_a = self.db["Activity"].aggregate(
            [
                {
                    "$group": {
                        "_id": {
                            "year_month": {'$substr': ['$start_date_time', 0, 7]},
                        },
                        "users": {
                            "$sum": 1
                        }
                    }
                },
                {
                    '$sort': {'users': -1}
                },
                {
                    '$limit': 1
                },
            ]
        )

        top_ym = list(result_a)
        most_pop = str(top_ym[0]['_id']['year_month'])
        # Saving the top year and month in separate variables to make task 9b easier.
        mp_year = int(most_pop[0:4])
        mp_month = int(most_pop[5:])
        print('\nMost popular year and month:\n', mp_year, ', ', mp_month)

        # b) Which user had the most activities this year and month, and how many recorded hours do they have?
        # Do they have more hours recorded than the user with the second most activities?
        print('\n\nSolution to query 9b:\n')
        result_b1 = self.db["Activity"].aggregate(
            [
                {
                    "$project": {
                        "_id": "$user_id",
                        "year": {'$year': ['$start_date_time']},
                        "month": {'$month': ['$start_date_time']},
                    }
                },
                {
                    '$match': {
                        'year': mp_year,
                        'month': mp_month}
                },
                {
                    '$group': {
                        '_id': '$_id',
                        'activities': {'$sum': 1}
                    }
                },
                {
                    '$sort': {'activities': -1}
                },
                {
                    '$limit': 2
                }
            ]
        )
        # Setting the limit to 2 in order to get both the user with the most activities,
        # and the user with the second most activities.
        print('Top 2 users with the most activities during most popular year/month-combo:')
        pprint(list(result_b1))
        id1 = '062'
        id2 = '014'

        result_b2 = self.db["Activity"].aggregate(
            [
                {
                    "$project": {
                        "_id": "$user_id",
                        "year": {'$year': ['$start_date_time']},
                        "month": {'$month': ['$start_date_time']},
                        # "start_time": "$start_date_time",
                        # "end_time": "$end_date_time",

                    }
                },
                {
                    '$match': {
                        '$and': [
                            {'year': mp_year},
                            {'month': mp_month},
                            {'$or': [{'_id': id1}, {'_id': id2}]}
                        ]
                        },
                },
            ]
        )

        print('\nHours recorded for these two users:')
        pprint(list(result_b2))

    # Find the total distance (in km) walked in 2008, by user with id=112.
    def query10(self):
        print('\n\nSolution to query 10:\n')
        tp_list = self.db['Activity'].aggregate([
            {'$match': {
                '$and': [
                    {'user_id': '112'},
                    {'transportation_mode': 'walk'},
                    {'$expr': {'$and': [{'$year': '$end_date_time'}, '2008']}}
                ]
            }
            },
            {'$lookup': {
                'from': 'TrackPoint',
                'localField': "_id",
                'foreignField': "activity_id",
                'as': 'trackPoint'
            }
            },
            {'$project': {
                'lat': '$trackPoint.lat',
                'lon': '$trackPoint.lon',
            }}
        ])

        tp_list = list(tp_list)

        total_distance = 0
        for activity in tp_list:
            number_of_tp = len(activity['lon'])
            for j in range(0, number_of_tp - 1):
                lat = activity['lat'][j]
                lon = activity['lon'][j]
                total_distance += haversine((lat, lon), (activity['lat'][j + 1], activity['lon'][j + 1]))
        print(round(total_distance), 'km')

    # Find the top 20 users who have gained the most altitude meters.
    def query11(self):
        print('\n\nSolution to query 11:\n')

    # Find all users who have invalid activities, and the number of invalid activities per user
    def query12(self):
        print('\n\nSolution to query 12:\n')


def main():
    program = None
    try:
        program = MongoQueryProgram()
        # program.query1()
        # program.query2()
        # program.query3()
        # program.query4()
        # program.query5()
        program.query6()
        # program.query7()
        # program.query8()
        # program.query9()
        # program.query10()
        # program.query11()
        # program.query12()
    except Exception as e:
        print("ERROR: Failed to use database:", e)
    finally:
        if program:
            program.connection.close_connection()


if __name__ == '__main__':
    main()
