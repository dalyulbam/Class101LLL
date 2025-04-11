# Flask 
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
app = Flask(__name__)
CORS(app)  # CORS 허용

##################################################################################
###################################### MYSQL #####################################
##################################################################################

# MySQL 
import os  
import mysql.connector 
from dotenv import load_dotenv  # python-dotenv 패키지에서 함수 가져오기
load_dotenv()


def db_connect():
    return mysql.connector.connect(
        host = os.environ.get('DB_HOST'),
        user= os.environ.get('DB_USER'),
        port = 3306,
        passwd= os.environ.get('DB_PASSWORD'),
        database = os.environ.get('DB_NAME'),
        # ssl_ca='./DigiCertGlobalRootCA.crt.pem',
    )

##################################################################################
################################# Block Chain ####################################
##################################################################################


@app.route("/")
def index():
    return render_template("index.html")

@app.route('/login')
def login():
    return render_template("login.html")

@app.route('/setNickname')
def set_nickname():
    return render_template("login_put_name.html")

@app.route('/explain')
def explain_game():
    return render_template("explain.html")

@app.route('/game')
def open_game():
    return render_template("game.html")

@app.route('/wallet', methods=['POST'])
def create_keys():
    wallet.create_keys()
    if wallet.save_keys():
        global blockchain
        blockchain = Blockchain(wallet.public_key, port)
        response = {
            'public_key': wallet.public_key,
            'private_key': wallet.private_key,
            'funds': blockchain.get_balance()
        }
        return jsonify(response), 201

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main_bp.index'))
    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = User(passphrase=form.passphrase.data)
            login_user(user)
            return redirect(url_for('main_bp.index'))
        except Exception as err:
            flash(err)
            return render_template('login.html', form=form)
    return render_template('login.html', form=form)

@app.route('/transaction', methods=['POST'])
def add_transaction():
    if wallet.public_key is None:
        return jsonify({'message': 'No wallet set up.'}), 400
    values = request.get_json()
    if not values or 'recipient' not in values or 'amount' not in values:
        return jsonify({'message': 'Required data is missing.'}), 400
    recipient = values['recipient']
    amount = values['amount']
    signature = wallet.sign_transaction(wallet.public_key, recipient, amount)
    success = blockchain.add_transaction(recipient, wallet.public_key, signature, amount)
    if success:
        response = {
            'message': 'Successfully added transaction.',
            'transaction': {
                'sender': wallet.public_key,
                'recipient': recipient,
                'amount': amount,
                'signature': signature
            },
            'funds': blockchain.get_balance()
        }
        return jsonify(response), 201
    
#For Game Generation 
@app.route('/randomHuman', methods=['GET'])
def get_rnd_human_data():
    mydbConnection = db_connect()
    cursor = mydbConnection.cursor()
    # 1st Execution 
    cursor.execute(f"SELECT COUNT(*) FROM {HUMAN_TABLE}")     
    rnd_results_res = cursor.fetchall()
    rnd_results = rnd_results_res[0][0] # random index 
    # 2nd Execution 
    cursor.execute(f"SELECT * FROM {HUMAN_TABLE} LIMIT 1 OFFSET {makeRandomIdx(rnd_results)}")
    results = cursor.fetchall()    
    print(results)
    # Finish 
    cursor.close()
    mydbConnection.close()
    return jsonify(results)

#For Game Generation 
@app.route('/randomEstateDataInRange', methods=['POST'])
def get_selective_estate_data01():

    results = []; same_region = True; selected_multiple_region = []

    def is_same_address(results):
        if results[0][0].strip() == results[1][0].strip(): return True; 
        else : return False;  

    def is_good_response(results):
        return not results or len(results) != 2 or is_same_address(results)

    try: 
        human_info = request.json
        #### Region Query #### 
        hope_area_split = human_info[0][0].split(" ")
        work_place = human_info[0][2]
        region_list = [reg_unit.strip() for reg_unit in hope_area_split if reg_unit.strip()]
        same_region, selected_multiple_region = check_multiple_territorial(bjd_df, region_list[-1], work_place)
        region_condition = regionName2condition(region_list)
        
        #### Price Query #### 
        wage = int(human_info[0][3])
        lower_value, upper_value = set_lower_upper_value_from_wage(region_list, wage)
        price_condition = f"price between {lower_value} AND {upper_value}"
        time_condition = f"dealdate between '2024-01-01' AND '2024-12-31'" # 2024년

        #### Cursor1 #### 
        mydbConnection = db_connect() 
        results = execute_adjustedCursor_with_condition( 
            reg_cond= region_condition, 
            price_cond= price_condition, 
            time_cond = time_condition,
            is_same_region= same_region,
            price_policy= True, 
            time_policy= True,
            table = ESTATE_TABLE, 
            selected_multiple_region= selected_multiple_region
        )

        #### Cursor2 #### 
        if is_good_response(results): 
            print("No boundary in it 1")
            price_condition = f"price between {lower_value * 0.65} and {upper_value * 1.5}"
            results = execute_adjustedCursor_with_condition(
                reg_cond= region_condition, 
                price_cond= price_condition,
                time_cond = time_condition, 
                is_same_region= same_region,
                table = ESTATE_TABLE, 
                price_policy= True, 
                time_policy= True,
                selected_multiple_region= selected_multiple_region
            )            

        #### Cursor3 #### 
        if is_good_response(results): 
            print("No boundary in it 2")
            price_condition = f"price between {lower_value * 0.3} and {upper_value * 2.0}"
            results = execute_adjustedCursor_with_condition(
                reg_cond= region_condition, 
                price_cond= price_condition, 
                time_cond = time_condition,
                is_same_region= same_region,
                table = ESTATE_TABLE, 
                price_policy= True, 
                time_policy= True,
                selected_multiple_region= selected_multiple_region
            )            

        #### Cursor4 #### 
        if is_good_response(results): 
            print("No boundary in it 3")
            results = execute_adjustedCursor_with_condition(
                reg_cond= region_condition, 
                price_cond= price_condition, 
                time_cond = time_condition,
                is_same_region= same_region,
                table = ESTATE_TABLE, 
                price_policy= False, 
                time_policy= True,
                selected_multiple_region= selected_multiple_region
            )            

        #### Final #### 
        mydbConnection.close()
    except Exception as err: 
        print(err)
    return jsonify(results)


#For Game Generation 
@app.route('/massiveRandomEstateDataInRange/<path:req_sample_num>', methods=['POST'])
def get_massive_selective_estate_data02(req_sample_num):
    try:
        req_sample_num = int(req_sample_num)  # Safely convert to integer
    except Exception as err:
        return [{"Error":err}]

    results = []; same_region = True; selected_multiple_region = []

    def is_same_address(results):
        if results[0][0].strip() == results[1][0].strip(): return True; 
        else : return False;  

    def is_good_response(results):
        return not results or len(results) != 2 or is_same_address(results)

    try: 
        human_info = request.json
        #### Region Query #### 
        hope_area_split = human_info[0][0].split(" ")
        work_place = human_info[0][2]
        region_list = [reg_unit.strip() for reg_unit in hope_area_split if reg_unit.strip()]
        same_region, selected_multiple_region = check_all_territorial_nearby(bjd_df, region_list[-1], work_place, sample_size = req_sample_num)
        region_condition = regionName2condition(region_list)
        
        #### Price Query #### 
        wage = int(human_info[0][3])
        lower_value, upper_value = set_lower_upper_value_from_wage(region_list, wage)
        price_condition = f"(price between {lower_value} and {upper_value})"
        time_condition = f"(dealdate between '2024-01-01' and '2024-12-31')" # 2024년

        #### Cursor1 #### 
        mydbConnection = db_connect() 
        results = massive_execute_with_condition( 
            reg_cond= region_condition, 
            price_cond= price_condition, 
            time_cond = time_condition,
            is_same_region= same_region,
            price_policy= True, 
            time_policy= True,
            table = ESTATE_TABLE, 
            selected_multiple_region= selected_multiple_region, 
            num_of_asset = req_sample_num
        )

        #### Cursor2 #### 
        if is_good_response(results): 
            print("No boundary in it 1")
            price_condition = f"price between {lower_value * 0.65} and {upper_value * 1.5}"
            results = massive_execute_with_condition(
                reg_cond= region_condition, 
                price_cond= price_condition, 
                time_cond = time_condition,
                is_same_region= same_region,
                table = ESTATE_TABLE, 
                price_policy= True, 
                time_policy= True,
                selected_multiple_region= selected_multiple_region,
                num_of_asset = req_sample_num
            )            

        #### Cursor3 #### 
        if is_good_response(results): 
            print("No boundary in it 2")
            price_condition = f"price between {lower_value * 0.3} and {upper_value * 2.0}"
            results = massive_execute_with_condition(
                reg_cond= region_condition, 
                price_cond= price_condition, 
                time_cond = time_condition,
                is_same_region= same_region,
                table = ESTATE_TABLE, 
                price_policy = True, 
                time_policy = True, 
                selected_multiple_region= selected_multiple_region,
                num_of_asset = req_sample_num
            )            

        #### Cursor4 #### 
        if is_good_response(results): 
            print("No boundary in it 3")
            results = massive_execute_with_condition(
                reg_cond= region_condition, 
                price_cond= price_condition, 
                time_cond = time_condition,
                is_same_region= same_region,
                table = ESTATE_TABLE, 
                price_policy= False, 
                time_policy = True, 
                selected_multiple_region= selected_multiple_region,
                num_of_asset = req_sample_num
            )            

        #### Final #### 
        mydbConnection.close()
    except Exception as err: 
        print(err)
        return [{"Error":err}]
    return jsonify(results)

@app.route('/gameResult', methods=['POST'])
def set_game_result():
    result_dict = request.json
    mydbConnection = db_connect()
    cursor = mydbConnection.cursor()
    sql = f"""
    INSERT INTO {GAME_TABLE}
    (asset1_address, asset1_aptname, asset1_housing, asset1_price, asset1_deposit, asset1_approval_date, 
    asset1_gen_num, asset1_space, asset1_floor, asset1_subway, asset1_latitude, asset1_longitude, asset1_dealdate,
    asset2_address, asset2_aptname, asset2_housing, asset2_price, asset2_deposit, asset2_approval_date, asset2_dealdate,
    asset2_gen_num, asset2_space, asset2_floor, asset2_subway, asset2_latitude, asset2_longitude,
    hope_place, age, workplace, wage, possession, fam_num, liquid_asset, 
    game_player, game_win_asset, game_time_sec, game_play_time)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    cursor.execute(sql, (
            result_dict["asset1_address"], result_dict["asset1_aptname"], result_dict["asset1_housing"], 
            result_dict["asset1_price"], result_dict["asset1_deposit"], result_dict["asset1_approval_date"], result_dict["asset1_gen_num"], 
            result_dict["asset1_space"], result_dict["asset1_floor"], result_dict["asset1_subway"],
            result_dict["asset1_latitude"], result_dict["asset1_longitude"], result_dict["asset1_dealdate"], 
            result_dict["asset2_address"], result_dict["asset2_aptname"], result_dict["asset2_housing"],
            result_dict["asset2_price"], result_dict["asset2_deposit"], result_dict["asset2_approval_date"], result_dict["asset2_gen_num"], 
            result_dict["asset2_space"], result_dict["asset2_floor"], result_dict["asset2_subway"], 
            result_dict["asset2_latitude"], result_dict["asset2_longitude"], result_dict["asset2_dealdate"],
            result_dict["hope_place"], result_dict["age"], result_dict["workplace"], result_dict["wage"], 
            result_dict["possession"], result_dict["fam_num"], result_dict["liquid_asset"],
            result_dict["game_player"], result_dict["game_win_asset"], result_dict["game_time_sec"], result_dict["game_play_time"],
            
        ))     
    results = cursor.fetchall()
    mydbConnection.commit()
    cursor.close()
    mydbConnection.close()
    return jsonify(results)




if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # 환경 변수에서 포트 가져오기, 없으면 기본 포트 5000
    print(f"Server is running on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)