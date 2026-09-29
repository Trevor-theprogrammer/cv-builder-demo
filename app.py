import logging
import os
import time
import uuid

from dotenv import load_dotenv
from flask import Flask, g, jsonify, render_template, request
from openai import APIConnectionError, APIStatusError, AuthenticationError, OpenAI, OpenAIError, RateLimitError

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


@app.before_request
def setup_request_trace():
    g.request_id = str(uuid.uuid4())
    g.request_started_at = time.perf_counter()
    app.logger.info(
        "request start method=%s path=%s request_id=%s",
        request.method,
        request.path,
        g.request_id,
    )


@app.after_request
def finalize_request_trace(response):
    duration_ms = (time.perf_counter() - g.request_started_at) * 1000
    response.headers["X-Request-ID"] = g.request_id
    app.logger.info(
        "request end method=%s path=%s status=%s duration_ms=%.2f request_id=%s",
        request.method,
        request.path,
        response.status_code,
        duration_ms,
        g.request_id,
    )
    return response


@app.post("/api/generate")
def generate_document():
	payload = request.get_json(silent=True)
	if not isinstance(payload, dict):
		return jsonify(error="Submit the form as JSON."), 400

	fields = {
		"name": (payload.get("name"), 120),
		"role": (payload.get("role"), 160),
		"skills": (payload.get("skills"), 1200),
		"experience": (payload.get("experience"), 3000),
		"education": (payload.get("education"), 1200),
	}
	profile = {
		key: value.strip()[:limit] if isinstance(value, str) else ""
		for key, (value, limit) in fields.items()
	}
	if not profile["name"] or not profile["role"] or not profile["skills"]:
		return jsonify(error="Add your name, target role, and skills to continue."), 400
	if not profile["experience"] and not profile["education"]:
		return jsonify(error="Add experience or education so the draft has useful context."), 400

	document_type = payload.get("document_type", "cover_letter")
	if not isinstance(document_type, str) or document_type not in {"cover_letter", "cv"}:
		return jsonify(error="Choose a CV or cover letter."), 400

	if not os.getenv("OPENAI_API_KEY"):
		return jsonify(error="AI is not configured yet. Set OPENAI_API_KEY in your local environment and restart the app."), 503

	document_names = {"cover_letter": "cover letter", "cv": "CV"}
	document_name = document_names[document_type]
	user_details = "\n".join(
		f"{label}: {profile[key]}"
		for key, label in (
			("name", "Name"),
			("role", "Target role"),
			("skills", "Skills"),
			("experience", "Experience"),
			("education", "Education"),
		)
		if profile[key]
	)

	if document_type == "cover_letter":
		instructions = (
			"Write a tailored, professional cover letter in plain text, around 250-350 words. "
			"Use a clear greeting, 3-4 concise paragraphs, and a sign-off. Do not invent "
			"employers, achievements, qualifications, or metrics. Use only the supplied facts."
		)
	else:
		instructions = (
			"Create a concise, ATS-friendly CV in plain text with sections for professional "
			"summary, skills, experience, and education. Use only supplied facts; do not "
			"invent employers, dates, qualifications, achievements, or metrics. Mark missing "
			"details with [Add details] rather than making them up."
		)

	try:
		client = OpenAI(timeout=45.0)
		completion = client.chat.completions.create(
			model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
			messages=[
				{"role": "system", "content": instructions},
				{"role": "user", "content": f"Draft a {document_name} from these details:\n{user_details}"},
			],
		)
		document = completion.choices[0].message.content
		if not document or not document.strip():
			return jsonify(error="The AI returned an empty draft. Please try again."), 502
		return jsonify(document=document.strip(), document_type=document_type)
	except AuthenticationError:
		return jsonify(error="The API key was rejected. Check OPENAI_API_KEY and restart the app."), 503
	except RateLimitError:
		return jsonify(error="The AI service is rate-limited or out of quota. Check your provider account and try again."), 429
	except APIConnectionError:
		return jsonify(error="Could not reach the AI service. Check your internet connection and try again."), 502
	except APIStatusError:
		return jsonify(error="The AI service could not complete this draft. Check the configured model and try again."), 502
	except OpenAIError:
		return jsonify(error="The AI service returned an unexpected error. Please try again."), 502


@app.route('/')
def home():
	return render_template('index.html', ai_configured=bool(os.getenv("OPENAI_API_KEY")))

if __name__ == '__main__':
	app.run(debug=True)
