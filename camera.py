import os
import time
import uuid

import requests
import base64

#百度云 人脸检测 申请信息
#唯一必须填的信息就这三行
APP_ID = "10906445"
API_KEY = "KDzuWSOUGLGPQjhUGf82bkVv"
SECRET_KEY = "ShoiNvRDqSrLZIGhfjWdrE6098I8RK1s"

FACE_GROUP_ID = "group_2"

IMAGE_DIR = "source_images"
DIR = "results"

def check_quality(face_detail):
    '''
    检测人脸质量
    1. 人脸置信度 face_probability
    2. 遮挡范围 occlusion
    3. 模糊度范围 blur
    4. 光照范围 illumination
    5. 姿态角度 pitch / roll / yaw
    6. 人脸大小
    '''
    if face_detail["face_probability"] < 0.6:
        return False

    quality = face_detail["quality"]
    occlusion = quality["occlusion"]
    if occlusion["left_eye"] > 0.6 or occlusion["right_eye"] > 0.6 or occlusion["nose"] > 0.7 or occlusion["mouth"] > 0.7 or occlusion["left_cheek"] > 0.8 or occlusion["right_cheek"] > 0.8 or occlusion["chin_contour"] > 0.6:
        print("occlusition fail")
        return False

    if quality["blur"] > 0.7:
        print("blur fail")
        return False

    if quality["illumination"] < 40:
        print("illumination fail")
        return False

    angle = face_detail["angle"]
    if abs(angle["yaw"]) > 35 or abs(angle["roll"]) > 35 or abs(angle["pitch"]) > 35:
        print("roll fail")
        return False

    location = face_detail["location"]
    if location["width"] < 50 or location["height"] < 50:
        print("size fail")
        return False

    return True

def init_face_group(face_group_id, token):
    try:
        URL = "https://aip.baidubce.com/rest/2.0/face/v3/faceset/group/add"
        params = { "access_token": token }
        data = { "group_id": face_group_id }
        s = requests.post(URL, params=params, data=data)
        r = s.json()
        if r["error_code"] != 0 and r["error_code"] != 223101:
            raise Exception("create face group fail. " + r)
    except Exception as e:
        print("init face group fail. " + url)
        raise e

def register_face(face_token, token, group_id, user_id):
    try:
        URL = "https://aip.baidubce.com/rest/2.0/face/v3/faceset/user/add"
        params = { "access_token": token }
        data = {
                "group_id": group_id,
                "user_id": user_id,
                "image_type": "FACE_TOKEN",
                "image": face_token
                }
        s = requests.post(URL, params=params, data=data)
        return s.json()
    except Exception as e:
        print("register face fail. " + url)
        raise e

def search_face(face_token, token, group_id):
    try:
        URL = "https://aip.baidubce.com/rest/2.0/face/v3/search"
        params = { "access_token": token }
        data = {
                "group_id_list": group_id,
                "image_type": "FACE_TOKEN",
                "image": face_token
                }
        s = requests.post(URL, params=params, data=data)
        return s.json()
    except Exception as e:
        print("search face fail. " + url)
        raise e

def detect_face(image, token):
    try:
        URL = "https://aip.baidubce.com/rest/2.0/face/v3/detect"
        params = { "access_token": token }
        data = {
                "face_field": "quality,age,gender",
                "image_type": "BASE64",
                "max_face_num": "5",
                "image": base64.b64encode(image)
                }
        s = requests.post(URL, params=params, data=data)
        return s.json()["result"]
    except Exception as e:
        print("detect face fail. " + url)
        raise e

def fetch_auth_token(api_key, secret_key):
    try:
        URL = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
                "grant_type": "client_credentials",
                "client_id": api_key,
                "client_secret": secret_key
                }
        s = requests.post(URL, params=params)
        return s.json()["access_token"]
    except Exception as e:
        print("fetch baidu auth token fail. " + url)
        raise e

def init_face_interfaces():
    # 百度云 V3 版本接口，需要先获取 access token   
    # token 30 天内有效，长期持续运行需要更新 token
    token = fetch_auth_token(API_KEY, SECRET_KEY)
    init_face_group(FACE_GROUP_ID, token)
    def detective(image):
        # 直接使用 HTTP 请求
        r = detect_face(image, token)
        #如果没有检测到人脸
        if r is None or r["face_num"] == 0:
            return []

        faces = {}
        for face in r["face_list"]:
            if not check_quality(face):
                continue
            faces[face["face_token"]] = face
        
        results = []
        for face_token in faces:
            search_result = search_face(face_token, token, FACE_GROUP_ID)

            if search_result["error_code"] == 222207:
                # 新人脸，注册新 id
                user_id = str(uuid.uuid1()).replace("-", "")
            elif search_result["error_code"] == 0:
                target_info = search_result["result"]["user_list"][0]
                if target_info["score"] < 60:
                    user_id = str(uuid.uuid1()).replace("-", "")
                else:
                    user_id = target_info["user_id"]
            else:
                # error. skip
                continue
            face = faces[face_token]
            results.append((user_id, face["gender"]["type"], face["age"]))

            # 忽略注册人脸是否成功
            register_face(face_token, token, FACE_GROUP_ID, user_id)
        return results

    return detective

def init_env():
    if not os.path.exists(DIR):
        os.makedirs(DIR)

def input_images():
    inputs = [f for f in os.listdir(IMAGE_DIR) if os.path.isfile(os.path.join(IMAGE_DIR, f)) and f.endswith("jpg")]
    def comparetor(v):
        return int(v.split(".")[0])
    return sorted(inputs, key=comparetor)

def load_image(filename):
    with open(filename, "rb") as fd:
        return fd.read()

def store_result(filename, content):
    with open(os.path.join(DIR, filename), "wb") as fd:
        fd.write(content)

init_env()
face_detective = init_face_interfaces()

inputs = input_images()

'''
image = load_image("./source_images/5.jpg")
r = face_detective(image)
print(r)
'''

for input in inputs:
    timestamp = int(input.split(".")[0])

    image = load_image(os.path.join(IMAGE_DIR, input))
    results = face_detective(image)
    
    print(timestamp, results)
    if len(results) == 0:
        store_result("{0}.jpg".format(timestamp), image)
    else:
        for result in results:
            store_result("{0}_{1}_{2}_{3}.jpg".format(timestamp, result[0], result[1], result[2]), image)

    time.sleep(0.3)

