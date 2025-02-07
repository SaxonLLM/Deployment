from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

def load_data(filename):
    """Loads prompts and responses from the specified text file"""
    data = []
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read()
            prompt_sections = content.split("--------------------------------------------------")

            for section in prompt_sections:
                section = section.strip()
                if section.startswith("Prompt"):
                    data.append(section)
    except FileNotFoundError:
        return []
    
    return data

def calculate_prompt_number(iteration, prompt_number):
    return (iteration - 1) * 7 + prompt_number

@app.route('/')
def index():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Prompt Viewer</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                padding: 20px;
                margin: 0 auto;
                max-width: 900px;
                line-height: 1.6;
            }
            /* Styling the tabs */
            .tabs {
                display: flex;
                cursor: pointer;
                padding: 10px;
                justify-content: space-around;
                background-color: #f1f1f1;
                margin-bottom: 20px;
            }
            .tab {
                padding: 10px 20px;
                background-color: #ddd;
                border-radius: 5px;
                margin-right: 10px;
                text-align: center;
            }
            .tab:hover {
                background-color: #bbb;
            }
            .active-tab {
                background-color: #7c7c7c;
                color: white;
            }
            /* Styling for hidden sections */
            .content-section {
                display: none;
            }
            .active-content {
                display: block;
            }

            #response-container {
                display: flex;
                justify-content: flex-start;
                margin-top: 20px;
            }
            #response {
                padding: 15px;
                background-color: #f1f1f1;
                border-radius: 5px;
                white-space: pre-wrap;
                word-wrap: break-word;
                width: 100%;
                max-width: 800px;
                text-align: left;
                box-sizing: border-box;
                overflow: hidden;
            }

            select, button {
                margin: 5px;
                padding: 5px;
            }

            h1, p, form {
                text-align: left;
            }
        </style>
    </head>
    <body>
        <h1>An attempt at SäxyLLM</h1>

        <!-- Tabs for Instructions and Prompt Selection -->
        <div class="tabs">
            <div id="instructionsTab" class="tab active-tab" onclick="showTab('instructions')">Read Instructions</div>
            <div id="promptsTab" class="tab" onclick="showTab('prompts')">Try it out!</div>
        </div>

        <!-- Instructions Section -->
        <div id="instructions" class="content-section active-content">
            <p>
            <h2>Models</h2>
            There are following 3 Models:<br>
            <b>Scraped Raw (SR):</b> Raw scraped data only stored *.txt file file <br>
            <b>Scraped Instrcut (SI):</b> Instruct Dataset made from the raw scraped data stored in *.jsonl fileformat.<br>
            <b>Scraped Syntetic Instrcut (SI):</b> Everything in SI + Dataset created syntetically by large-scale commerical LLMs. <br>
            </p>

            <p>
            <h2>Tasks</h2>
            All 3 models are asked to do the following tasks:<br>
            <b>Story Task:</b> Answer in Sächsisch: Write a short story about two Saxons in the Deutsche Bahn. <br>
            <b>Translation Task:</b> Translate to Sächsisch: 'Our team consists of more than 180 people, including renowned international ...' <br>
            <b>History Task:</b> Answer in Sächsisch: What is the history of TU Dresden? <br>
            <b>Saying Hello:</b> How do you say 'Good Morning' in Sächsisch? <br>
            </p>
            
            <p>
            <h2>Prompt Engineering</h2>
            These questions are also tried with promt engineering where, before asking it to do the task, we prompt the LLM as follows:<br>
            <b>Story:</b> You are a Sächsisch storywriter who only writes in Sächsisch. You don't speak any English. You don't speak Hochdeutsch. Donot answer in English and Donot answer in Hochdeutsch.<br>
            <b>Translation:</b>  You are a English to Sächsisch translator who only writes in Sächsisch. You don't speak any English. You don't speak Hochdeutsch. Donot answer in English and Donot answer in Hochdeutsch. <br>
            <b>History:</b> You are a Sächsisch historian who only writes in Sächsisch. You don't speak any English. You don't speak Hochdeutsch. Donot answer in English and Donot answer in Hochdeutsch.<br>
            </p>
            
            <h2>Iterations</h2>
            <p> For each prompt and model combination, there are 5 iterations provided to observe the variation while feeding the same prompt does produce different results. </p>
        </div>

        <!-- Prompt Selection Section -->
        <div id="prompts" class="content-section">
            <form id="promptForm">
                <label for="model">Choose a model:</label>
                <select name="model" id="model">
                    <option value="SI">SI</option>
                    <option value="SR">SR</option>
                    <option value="SSR">SSR</option>
                </select>

                <label for="prompt_number">Choose a prompt:</label>
                <select name="prompt_number" id="prompt_number">
                    {% for i in range(1, 8) %}
                        <option value="{{ i }}">
                            {% if i in [1] %}
                                Story + Prompt Engineering
                            {% elif i in [2] %}
                                Translation + Prompt Engineering
                            {% elif i in [3] %}
                                History + Prompt Engineering
                            {% elif i in [4] %}
                                Story
                            {% elif i in [5] %}
                                Translate
                            {% elif i in [6] %}
                                History
                            {% else %}
                                Saying Hello
                            {% endif %}
                        </option>
                    {% endfor %}
                </select>


                <label for="iteration">Choose iteration:</label>
                <select name="iteration" id="iteration">
                    {% for i in range(1, 6) %}
                        <option value="{{ i }}">{{ i }}</option>
                    {% endfor %}
                </select>
                <br>
                <button type="submit">View the Response</button>
            </form>

            <div id="response-container">
                <div id="response"></div>
            </div>
        </div>

        <script>
            // Function to switch between tabs
            function showTab(tab) {
                const instructionsTab = document.getElementById("instructionsTab");
                const promptsTab = document.getElementById("promptsTab");
                const instructionsSection = document.getElementById("instructions");
                const promptsSection = document.getElementById("prompts");

                if (tab === 'instructions') {
                    instructionsTab.classList.add("active-tab");
                    promptsTab.classList.remove("active-tab");
                    instructionsSection.classList.add("active-content");
                    promptsSection.classList.remove("active-content");
                } else {
                    instructionsTab.classList.remove("active-tab");
                    promptsTab.classList.add("active-tab");
                    instructionsSection.classList.remove("active-content");
                    promptsSection.classList.add("active-content");
                }
            }

            // Handle the form submission for getting response
            document.getElementById("promptForm").onsubmit = async function(e) {
                e.preventDefault();
                let formData = new FormData(e.target);
                let response = await fetch("/get_response", { method: "POST", body: formData });
                let data = await response.json();

                if (data.prompt) {
                    let formattedText = data.prompt.replace(/\\n/g, "<br>");
                    document.getElementById("response").innerHTML = `<p>${formattedText}</p>`;
                } else {
                    document.getElementById("response").innerHTML = "<p>Error retrieving response.</p>";
                }
            };
        </script>
    </body>
    </html>
    """
    return render_template_string(html_content)

@app.route('/get_response', methods=['POST'])
def get_response():
    model = request.form.get('model')  # Get selected model (SI, SR, SSR)
    prompt_number = int(request.form.get('prompt_number'))
    iteration = int(request.form.get('iteration'))
    
    # Determine which file to load
    filename = f"{model}.txt"
    data = load_data(filename)

    # Calculate the correct prompt index
    prompt_index = calculate_prompt_number(iteration, prompt_number)
    prompt_key = f"Prompt {prompt_index}"

    for prompt in data:
        if prompt.startswith(prompt_key):
            return jsonify({"prompt": prompt[len(prompt_key) + 2:]})

    return jsonify({"error": "Prompt not found"})

if __name__ == '__main__':
    app.run(debug=True)
