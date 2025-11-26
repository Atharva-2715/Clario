# create_sample_pdf.py
from reportlab.pdfgen import canvas
from pathlib import Path

# Define path relative to the project root directory
pdf_dir = Path("backend") / "data"
pdf_dir.mkdir(parents=True, exist_ok=True) # Ensure the directory exists

filename = pdf_dir / "sample_notes.pdf"

text_content = """
ARTIFICIAL INTELLIGENCE (AI)

Artificial Intelligence is a field of computer science that focuses on building systems
capable of performing tasks that normally require human intelligence. These tasks include:

• Learning
• Reasoning
• Problem-solving
• Understanding language
• Making decisions

AI is broadly divided into two categories:

1. Narrow AI – AI designed for a specific task (e.g., chatbots, recommendation systems).
2. General AI – AI that can perform any intellectual task like a human.

Applications of AI:
• Healthcare diagnosis
• Self-driving cars
• Smart assistants
• Fraud detection

PROBABILITY (MATH)

Conditional probability is the likelihood of an event occurring, given that another event
has already occurred. The formula is: P(A|B) = P(A and B) / P(B), where P(B) > 0.

Bayes' theorem is a formula that describes how to update the probabilities of hypotheses
when given evidence. It is foundational for many machine learning algorithms.

PHYSICS - MECHANICS

Newton's first law of motion states that an object remains in the state of rest or uniform
motion unless acted upon by an external unbalanced force. This is often called the law of inertia.
"""

# Create PDF
c = canvas.Canvas(str(filename)) # Convert back to string for reportlab
y_position = 800
line_height = 15

for line in text_content.split("\n"):
    c.drawString(50, y_position, line)
    y_position -= line_height
    if y_position < 50: # Handle page break if content is long
        c.showPage()
        y_position = 800

c.save()
print(f"Sample PDF created successfully at {filename}")