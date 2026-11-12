import os
import random
from datetime import datetime
from flask import Flask, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# Obtener la URL de Neon desde las variables de entorno de Render o local
DATABASE_URL = os.environ.get("DATABASE_URL")


def get_db_connection():
  conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
  return conn


@app.route("/", methods=["GET"])
def home():
  return jsonify({
      "estado": "activo",
      "mensaje": "API de Sistema de Gestión de Solicitudes funcionando correctamente",
  })


# Endpoint para consultar todas las solicitudes (o filtrar)
@app.route("/api/solicitudes", methods=["GET"])
def get_solicitudes():
  try:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM solicitudes ORDER BY fecha_creacion DESC;"
    )
    solicitudes = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(solicitudes), 200
  except Exception as e:
    return jsonify({"error": str(e)}), 500


# Endpoint para registrar una nueva solicitud desde n8n
@app.route("/api/solicitudes", methods=["POST"])
def create_solicitud():
  try:
    data = request.get_json()

    nombre = data.get("nombre_usuario")
    correo = data.get("correo_usuario")
    categoria = data.get("categoria")
    prioridad = data.get("prioridad")
    descripcion = data.get("descripcion")

    if not all([nombre, correo, categoria, prioridad, descripcion]):
      return jsonify({"error": "Faltan campos obligatorios"}), 400

    # Generar folio único (Ej: SUP-2026-8492)
    anio_actual = datetime.now().year
    aleatorio = random.randint(1000, 9999)
    folio = f"SUP-{anio_actual}-{aleatorio}"

    conn = get_db_connection()
    cur = conn.cursor()

    query = """
            INSERT INTO solicitudes (folio, nombre_usuario, correo_usuario, categoria, prioridad, descripcion, estado)
            VALUES (%s, %s, %s, %s, %s, %s, 'Pendiente')
            RETURNING id, folio, fecha_creacion;
        """
    cur.execute(
        query, (folio, nombre, correo, categoria, prioridad, descripcion)
    )
    nueva_solicitud = cur.fetchone()
    conn.commit()

    cur.close()
    conn.close()

    return (
        jsonify({
            "mensaje": "Solicitud registrada con éxito",
            "folio": nueva_solicitud["folio"],
            "id": nueva_solicitud["id"],
            "fecha": nueva_solicitud["fecha_creacion"],
        }),
        201,
    )

  except Exception as e:
    return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
  app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))