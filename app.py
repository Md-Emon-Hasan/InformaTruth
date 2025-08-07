from flask import Flask
from flask import render_template
from flask import request
from flask import jsonify
from models.loader import ModelLoader
from models.classifier import Classifier
from graph.builder import PipelineBuilder

app = Flask(__name__)

# Initialize models once
model_loader = ModelLoader()
model_loader.load_models()
classifier = Classifier(model_loader.roberta_tokenizer, model_loader.roberta_model)
pipeline = PipelineBuilder.build_graph(classifier, model_loader.flan_tokenizer, model_loader.flan_model)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    input_type = data['inputType']
    content = data['content']
    
    result = pipeline.invoke({
        "input_type": input_type,
        "value": content
    })
    
    return jsonify({
        "label": result["label"],
        "confidence": f"{result['confidence']:.2f}",
        "explanation": result["explanation"]
    })

if __name__ == '__main__':
    app.run(debug=True)