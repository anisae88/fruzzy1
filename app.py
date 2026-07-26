import matplotlib
matplotlib.use('Agg')

from flask import Flask, render_template, request, redirect, url_for
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
import io, base64

app = Flask(__name__)

# =========================
# FUNGSI KEANGGOTAAN
# =========================
def linear_up(x, a, b):
    if x <= a:
        return 0
    elif x >= b:
        return 1
    else:
        return (x - a) / (b - a)

def linear_down(x, a, b):
    if x <= a:
        return 1
    elif x >= b:
        return 0
    else:
        return (b - x) / (b - a)


# =========================
# GRAFIK
# =========================
def plot_input_membership():

    # ================= SUHU =================
    fig, ax = plt.subplots()

    x_suhu = np.linspace(0, 50, 200)

    dingin = [linear_down(i, 20, 30) for i in x_suhu]
    panas = [linear_up(i, 25, 40) for i in x_suhu]

    ax.plot(x_suhu, dingin, label="Dingin")
    ax.plot(x_suhu, panas, label="Panas")

    ax.set_title("Fungsi Keanggotaan Suhu")
    ax.set_xlabel("Suhu (°C)")
    ax.set_ylabel("Derajat Keanggotaan")
    ax.legend()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_suhu = base64.b64encode(buf.getvalue()).decode()
    plt.close('all')


    # ================= KELEMBABAN =================
    fig, ax = plt.subplots()

    x_lembab = np.linspace(0, 100, 200)

    kering = [linear_down(i, 40, 70) for i in x_lembab]
    lembab = [linear_up(i, 50, 90) for i in x_lembab]

    ax.plot(x_lembab, kering, label="Kering")
    ax.plot(x_lembab, lembab, label="Lembab")

    ax.set_title("Fungsi Keanggotaan Kelembaban")
    ax.set_xlabel("Kelembaban (%)")
    ax.set_ylabel("Derajat Keanggotaan")
    ax.legend()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_lembab = base64.b64encode(buf.getvalue()).decode()
    plt.close('all')

    return img_suhu, img_lembab
def plot_fuzzy(suhu, kelembaban):

    fig, axs = plt.subplots(1, 2, figsize=(10,4))

    # ================= SUHU =================
    x = np.linspace(0, 50, 200)

    dingin = [linear_down(i, 20, 30) for i in x]
    panas = [linear_up(i, 25, 40) for i in x]

    axs[0].plot(x, dingin, label="Dingin")
    axs[0].plot(x, panas, label="Panas")
    axs[0].axvline(suhu)
    axs[0].set_title("Fuzzifikasi Suhu")
    axs[0].legend()

    # ================= KELEMBABAN =================
    x2 = np.linspace(0, 100, 200)

    kering = [linear_down(i, 40, 70) for i in x2]
    lembab = [linear_up(i, 50, 90) for i in x2]

    axs[1].plot(x2, kering, label="Kering")
    axs[1].plot(x2, lembab, label="Lembab")
    axs[1].axvline(kelembaban)
    axs[1].set_title("Fuzzifikasi Kelembaban")
    axs[1].legend()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    img = base64.b64encode(buf.getvalue()).decode('utf-8')

    plt.close('all')

    return img
# =========================
# TSUKAMOTO
# =========================

def tsukamoto(suhu, kelembaban):

    # =========================
    # FUZZIFIKASI
    # =========================
    dingin = linear_down(suhu, 20, 30)
    panas = linear_up(suhu, 25, 40)

    kering = linear_down(kelembaban, 40, 70)
    lembab = linear_up(kelembaban, 50, 90)

    # =========================
    # RULE (4 RULE)
    # =========================

    # R1: dingin & kering → lambat
    a1 = min(dingin, kering)
    z1 = 20 + a1 * (40 - 20)

    # R2: dingin & lembab → sedang
    a2 = min(dingin, lembab)
    z2 = 40 + a2 * (70 - 40)

    # R3: panas & kering → sedang
    a3 = min(panas, kering)
    z3 = 40 + a3 * (70 - 40)

    # R4: panas & lembab → cepat
    a4 = min(panas, lembab)
    z4 = 70 + a4 * (100 - 70)

    # =========================
    # DEFUZZIFIKASI
    # =========================
    pembilang = (a1*z1) + (a2*z2) + (a3*z3) + (a4*z4)
    penyebut = a1 + a2 + a3 + a4

    if penyebut == 0:
        z = 50  # fallback
    else:
        z = pembilang / penyebut

    return z, {
        "dingin": dingin,
        "panas": panas,
        "kering": kering,
        "lembab": lembab,
        "a1": a1,
        "a2": a2,
        "a3": a3,
        "a4": a4,
        "z1": z1,
        "z2": z2,
        "z3": z3,
        "z4": z4
    }

def plot_defuzzy(z):
    fig, ax = plt.subplots()

    x = np.linspace(0, 100, 200)

    lambat = [linear_down(i, 20, 50) for i in x]
    cepat = [linear_up(i, 50, 100) for i in x]

    ax.plot(x, lambat)
    ax.plot(x, cepat)
    ax.axvline(z)

    ax.set_title("Defuzzifikasi")

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img = base64.b64encode(buf.getvalue()).decode()
    plt.close()

    return img
def plot_3d_surface():

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    suhu_range = np.linspace(15, 45, 30)
    kelembaban_range = np.linspace(30, 100, 30)

    X, Y = np.meshgrid(suhu_range, kelembaban_range)
    Z = np.zeros_like(X)

    for i in range(len(suhu_range)):
        for j in range(len(kelembaban_range)):
            z, _ = tsukamoto(X[j, i], Y[j, i])  # ambil hanya z
            Z[j, i] = z

    ax.plot_surface(X, Y, Z)

    ax.set_xlabel('Suhu')
    ax.set_ylabel('Kelembaban')
    ax.set_zlabel('Kecepatan Kipas')

    ax.set_title("Surface Fuzzy Tsukamoto")

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    img = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close()

    return img

# =========================
# ROUTES
# =========================

@app.route("/")
def index():

    plot_suhu, plot_lembab = plot_input_membership()

    return render_template("index.html",
                           plot_suhu=plot_suhu,
                           plot_lembab=plot_lembab)

@app.route("/tambah")
def tambah():
    return render_template("tambah_data.html")

@app.route("/proses", methods=["POST"])
def proses():

    suhu = float(request.form["suhu"])
    kelembaban = float(request.form["kelembaban"])

    scaler = MinMaxScaler()
    data = np.array([[suhu], [kelembaban]])
    scaler.fit(data)
    scaler.transform(data)

    # 🔥 PANGGIL SEKALI SAJA
    hasil, detail = tsukamoto(suhu, kelembaban)

    plot1 = plot_fuzzy(suhu, kelembaban)
    plot2 = plot_defuzzy(hasil)
    plot3d = plot_3d_surface()

    return render_template("hasil.html",
                    suhu=suhu,
                    kelembaban=kelembaban,
                    hasil=round(hasil,2),
                    detail=detail,
                    plot1=plot1,
                    plot2=plot2,
                    plot3d=plot3d)

if __name__ == "__main__":
    app.run(debug=True)
