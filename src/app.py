import fastapi as fs


app = fs.FastAPI()



@app.get("/")
def arey():
    return "Saga home page data"

@app.get("/about")
def about():
    return "about data"

@app.get("/register")
def register():
    return "Registration process"
