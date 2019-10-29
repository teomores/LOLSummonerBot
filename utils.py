#############################
### Neo4j Utils Functions ###
#############################

def create_user_instance(tx, chat_id):
    for record in tx.run("MATCH (ui:UserInstance) WHERE ui.chat_id=$chat_id RETURN count(ui)", chat_id=chat_id):
        if record['count(ui)'] == 0:
            print(f"Creating user {chat_id}.")
            tx.run("CREATE (n:UserInstance {chat_id: $chat_id})", chat_id=chat_id)
        else:
            print(f'User {chat_id} already in db.')

def create_summoner_instance(tx, summoner_id):
    for record in tx.run("MATCH (si:SummonerInstance) WHERE si.summoner_id=$summoner_id RETURN count(si)", summoner_id=summoner_id):
        if record['count(si)'] == 0:
            print(f"Creating summoner {summoner_id}.")
            tx.run("CREATE (si:SummonerInstance {summoner_id: $summoner_id})", summoner_id=summoner_id)
        else:
            print(f'Summoner {summoner_id} already in db.')

def connect_user_summoner(tx, chat_id, summoner_id):
    for record in tx.run("MATCH (si:SummonerInstance {summoner_id:$summoner_id})<-[:SUBSCRIBED_TO]-(ui:UserInstance {chat_id:$chat_id}) RETURN count(ui)", summoner_id=summoner_id, chat_id=chat_id):
        if record['count(ui)'] == 0:
            print(f"Subscribing {chat_id} to {summoner_id}...")
            tx.run("MATCH (ui:UserInstance) WHERE ui.chat_id =$chat_id MATCH (si:SummonerInstance) WHERE si.summoner_id =$summoner_id CREATE (ui)-[:SUBSCRIBED_TO]->(si)", chat_id=chat_id, summoner_id=summoner_id)
            print(f"{chat_id} is now subscribed to {summoner_id}.")
        else:
            print(f"{chat_id} already subscribed to {summoner_id}")

def get_subscribers(tx, summoner_id):
    subscribers = []
    for record in tx.run("MATCH (si:SummonerInstance {summoner_id:$summoner_id})<-[:SUBSCRIBED_TO]-(ui) RETURN ui", summoner_id=summoner_id):
        #print(record["ui"]['chat_id'])
        subscribers.append(record["ui"]['chat_id'])
    return subscribers

def get_subscriptions(tx, chat_id):
    subscriptions = []
    for record in tx.run("MATCH (ui:UserInstance {chat_id:$chat_id})-[:SUBSCRIBED_TO]->(si) RETURN si", chat_id=chat_id):
        #print(record["si"]['summoner_id'])
        subscriptions.append(record["si"]['summoner_id'])
    return subscriptions

def delete_sub_user_summoner(tx, chat_id, summoner_id):
    for record in tx.run("MATCH (si:SummonerInstance {summoner_id:$summoner_id})<-[:SUBSCRIBED_TO]-(ui:UserInstance {chat_id:$chat_id}) RETURN count(ui)", summoner_id=summoner_id, chat_id=chat_id):
        if record['count(ui)'] == 1:
            print(f'Unsubscribing {chat_id} from {summoner_id}...')
            tx.run("MATCH (ui:UserInstance {chat_id:$chat_id})-[s:SUBSCRIBED_TO]->(si:SummonerInstance {summoner_id:$summoner_id}) DELETE s", chat_id=chat_id,  summoner_id=summoner_id)
            print(f"{chat_id} unsubscribed from {summoner_id}")
        elif record['count(ui)'] == 0:
            print(f"{chat_id} was not subscribed to {summoner_id}")
        else:
            print(f"ERROR: detected multiple subscriptions from {chat_id} to {summoner_id}")

def delete_all_subs(tx, chat_id):
    tx.run("MATCH (ui:UserInstance {chat_id:$chat_id})-[s:SUBSCRIBED_TO]->(si:SummonerInstance) DELETE s", chat_id=chat_id)
    print("All your subs are now deleted.")

def delete_summoner(tx, summoner_id):
    # this is called when a summoner has no active subscribers
    tx.run("MATCH (si:SummonerInstance {summoner_id:$summoner_id}) DELETE si", summoner_id=summoner_id)
    print(f"Summoner {summoner_id} deleted because it has no active subscriptions.")

def get_all_summoners(tx):
    summoner_list = []
    for record in tx.run("MATCH (si:SummonerInstance) RETURN si.summoner_id"):
        subs = get_subscribers(tx, record['si.summoner_id'])
        #print(f"subs of {record['si.summoner_id']}:")
        #print(*subs)
        if len(subs) == 0:
            delete_summoner(tx, record['si.summoner_id'])
        summoner_list.append(record['si.summoner_id'])
    return summoner_list
