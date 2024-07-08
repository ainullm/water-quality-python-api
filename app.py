from flask import Flask, jsonify, request
import numpy as np
import random
from time import sleep

app = Flask(__name__)

# Initialize threshold values with defaults
thresholds = {
    "suhu_min": 28,
    "suhu_max": 32,
    "do_min": 4,
    "do_max": 10,
    "ph_min": 7.5,
    "ph_max": 8.5,
    "salinitas_min": 5,
    "salinitas_max": 40
}

def defuzzify_tfns(tfns):
    return np.sum(tfns) / len(tfns)

@app.route('/set-thresholds', methods=['POST'])
def set_thresholds():
    global thresholds
    data = request.json
    for key in thresholds.keys():
        if key in data:
            thresholds[key] = data[key]
    return jsonify({"message": "Thresholds updated successfully", "thresholds": thresholds})

@app.route('/get-thresholds', methods=['GET'])
def get_thresholds():
    return jsonify(thresholds)

@app.route('/water-quality', methods=['POST'])
def assess_quality():
    # Data parameter from request
    data = request.json
    do = data['do']
    ph = data['ph']
    suhu = data['suhu']
    salinitas = data['salinitas']

    # Matriks perbandingan berpasangan (TFN)
    matriks_perbandingan = np.array([
        [1, 3, 5, 7],
        [1/3, 1, 3, 5],
        [1/5, 1/3, 1, 3],
        [1/7, 1/5, 1/3, 1]
    ])

    # Perhitungan bobot fuzzy
    bobot_fuzzy = []
    for i in range(len(matriks_perbandingan)):
        bobot_fuzzy.append(defuzzify_tfns(matriks_perbandingan[i]))

    # Normalisasi bobot fuzzy
    bobot_normal = bobot_fuzzy / np.sum(bobot_fuzzy)

    # Normalisasi nilai parameter
    nilai_normal = np.array([
        (do - thresholds['do_min']) / (thresholds['do_max'] - thresholds['do_min']),
        (ph - thresholds['ph_min']) / (thresholds['ph_max'] - thresholds['ph_min']),
        (suhu - thresholds['suhu_min']) / (thresholds['suhu_max'] - thresholds['suhu_min']),
        (salinitas - thresholds['salinitas_min']) / (thresholds['salinitas_max'] - thresholds['salinitas_min']),
    ])

    # Perhitungan nilai WSM
    nilai_wsm = np.dot(bobot_normal, nilai_normal)

    batas_wsm = {
        "Poor": (0, 0.33),
        "Medium": (0.33, 0.67),
        "Good": (0.67, 1)
    }

    # Define quality variable outside the loop
    quality = None

    # Loop to find the quality based on WSM value
    for key, value in batas_wsm.items():
        if value[0] <= nilai_wsm <= value[1]:
            quality = key
            break

    response = {
        "normalisasi_parameter": nilai_normal.tolist(),
        "bobot_fuzzy": bobot_fuzzy,
        "bobot_normal": bobot_normal.tolist(),
        "wsm": nilai_wsm,
        "quality": quality if quality is not None else "Poor"
    }

    return jsonify(response)

# @app.route('/get-monitoring', methods=['GET'])
# def monitoring_dummy():
#     # Simulasi data acak
#     suhu = random.uniform(28, 32)
#     salinitas = random.uniform(5, 40)
#     ph = random.uniform(7.5, 8.5)
#     oksigen = random.uniform(3, 10)

#     # Buat dictionary data
#     data = {
#         "suhu": suhu,
#         "salinitas": salinitas,
#         "ph": ph,
#         "oksigen": oksigen
#     }

#     # Kembalikan data dalam format JSON
#     return jsonify(data)


@app.route('/get-monitoring', methods=['GET'])
def get_data():
    # Initialize variables
    current_temperature = 29
    current_salinity = 20
    current_ph = 8
    current_oxygen = 5

    # Generate random fluctuations with a bias
    temperature_change = random.uniform(-0.5, 0.5)
    salinity_change = random.uniform(-1, 1)
    ph_change = random.uniform(-0.1, 0.1)
    oxygen_change = random.uniform(-0.2, 0.2)

    # Update values with fluctuations
    new_temperature = current_temperature + temperature_change
    new_salinity = max(5, min(current_salinity + salinity_change, 40))
    new_ph = max(7.5, min(current_ph + ph_change, 8.5))
    new_oxygen = max(3, min(current_oxygen + oxygen_change, 10))

    # Update current values
    current_temperature = new_temperature
    current_salinity = new_salinity
    current_ph = new_ph
    current_oxygen = new_oxygen

    # Create data dictionary
    data = {
        "suhu": current_temperature,
        "salinitas": current_salinity,
        "ph": current_ph,
        "do": current_oxygen
    }

    # Return data in JSON format
    return jsonify(data)


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
