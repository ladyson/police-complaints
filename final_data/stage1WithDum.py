import pandas as pd
import psycopg2
import sys

def go(output_fn):
    '''Generate dataframe with features from database'''

    conn = psycopg2.connect("dbname = police user = lauren password = llc")

    #Queries for features
    alleg = "SELECT crid, a.officer_id, a.dateobj, (CASE WHEN a.finding_edit = 'No Affidavit' THEN 1 ELSE 0 END) AS no_affidavit,\
                tractce10, o.race_edit AS officer_race, o.gender AS officer_gender, \
                (CASE WHEN EXTRACT(dow FROM a.dateobj) NOT IN (0, 6) THEN 1 ELSE 0 END) AS weekend, \
                (CASE WHEN o.rank IS NOT NULL THEN o.rank ELSE 'UNKNOWN' END) AS rank, \
                (CASE WHEN investigator_name IN (SELECT concat_ws(', ', officer_last, officer_first) \
                FROM officers) THEN 1 ELSE 0 END) AS police_investigator \
                FROM allegations as a LEFT JOIN officers as o \
                ON (a.officer_id = o.officer_id) \
                LEFT JOIN investigators AS i ON (a.investigator_id = i.investigator_id) \
                WHERE tractce10 IS NOT NULL;"

    invest1 = "SELECT * FROM investigator_beat_dum1;"

    invest2 = "SELECT * FROM investigator_beat_dum2;"

    age = "SELECT crid, officer_id, officers_age, (officers_age^2) AS agesqrd FROM ages;"

    data311 = "SELECT * FROM time_distance_311;"

    datacrime = "SELECT * FROM time_distance_crime;"

    priors = "SELECT * FROM prior_complaints;"

    alleg_df = pd.read_sql(alleg, conn)
    invest1_df = pd.read_sql(invest1, conn)
    invest2_df = pd.read_sql(invest2, conn)
    age_df = pd.read_sql(age, conn)
    data311_df = pd.read_sql(data311, conn)
    datacrime_df = pd.read_sql(datacrime, conn)
    priors_df = pd.read_sql(priors, conn)
    #Close connection to database after queries

    conn.commit()
    conn.close()

    data311_df.drop_duplicates('crid', inplace = True)
    datacrime_df.drop_duplicates('crid', inplace = True)

    #Merge (join) dataframes on shared keys
    df_final = alleg_df.merge(invest1_df.drop('index', axis = 1), on = ['crid', 'officer_id'], how = 'left')\
                .merge(invest2_df.drop('index', axis = 1), on = ['crid', 'officer_id'], how = 'left')\
                .merge(age_df, on = ['crid', 'officer_id'], how = 'left')\
                .merge(data311_df, on = 'crid', how = 'left').merge(datacrime_df, on = 'crid', how = 'left')\
                .merge(priors_df, on = ['crid', 'officer_id'], how = 'left')

    #Dummies for race and rank and drop unneeded columns
    rank_dummies = pd.get_dummies(df_final['rank'], prefix = 'Rank', prefix_sep = ' ', dummy_na = True)
    gender_dummies = pd.get_dummies(df_final[['officer_id', 'officer_race', 'officer_gender']], prefix = 'Officer', prefix_sep = ' ', dummy_na = True)

    df_final = pd.concat([df_final, rank_dummies, gender_dummies], axis = 1)
    df_final.drop(['crid', 'tract_1', 'tractce10', 'officer_race', 'rank', 'officer_gender', 'officer_id'], axis = 1, inplace = True)

    df_final.to_csv(output_fn)

if __name__ == '__main__':
    go(sys.argv[1])
