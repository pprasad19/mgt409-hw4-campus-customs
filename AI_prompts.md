# AI Prompts

## Problem 1 - Vibe coder prompts

### Initial Prompts

I am going to breaking the assignment into various smaller prompts going forward. First, create an AI_prompts.md file. In this file, create headings titled Problems 1-13. For each of these headings, create subheadings "Initial Prompts" and "Follow-up Prompt". Do this now

### Follow-up Prompt

None was needed

## Problem 2 - Analyze the database

### Initial Prompts

Now look at the database data/campus_customs.db. You should be able to understand the fields of each table. At the minimum, make sure you understand users, catalogue, and inventory. Then, start the output/harness.md file. In this file, each tables and its corresponding fields should be written down. Also, one sentence regarding why this field matters for the shop should be included in the file as well. Please keep in mind that we will continue to update this harness as we work through this homework.

### Follow-up Prompt

None was needed

## Problem 3 - Build the Campus Customs website

### Initial Prompts

Now we will be going to Problem 3. Scaffold a react + vite + typescript front end for Campus Customs. There should be a nav bar at the top that links to the following main pages: Home, Products, About Us, Log In, and Create Account. For the Home and About Us pages, use the campus customs-style wording for https://yalebulldogblue.com/ as an example of what to write. The original site text should not be copied; you should use your own voice to write these pages. On the Products page, product images from the catalogue should be shown (use the image paths in the database) with basic product information such as name, price, and short description. Make sure that each product opens a single-item package (large image on one side, full product text on the other - description, price, sizes/stock when you have them). When a shopper clicks on a card on Products, they should be taken there. In the bottom right of the site, a chat interface should be added (a floating chat panel would be fine). It does not need to be able to talk to an agent yet since a stub being able to call your backend later is sufficient. A small API will be needed to read the database. so you can start a simple FastAPI app in backend/main.py to serve images and products. Later on in this assignment, we will grow it into the agent backend

### Follow-up Prompt

None was needed

## Problem 4 - Create account and log in

### Initial Prompts

Now we will be going to Problem 4. The goal of this problem is to build a normal create-account/login flow. When creating the account, a first name, last name, email, and password are needed. Also we should confirm that the password is a nice touch. When logging in, an email and password would be needed. New accounts should go to the users table. All passwords should be stored securely so that hackers (both AI and humans) cannot access them. There is already a seed database with a test user that you can use while building. The email is test@campuscustoms.yale.edu. The password is password. Please make sure that you can log in as this user, and that the brand-new account that you will create also works. The output/harness.md file should be updated with how authorization works (what you store for a user and how passwords are protected).

### Follow-up Prompt

**Follow-up 1** *(Claude's suggestion, quoted back to approve it)*

do this recommendation: sliding expiry — keep a short TTL but reissue the token on each authenticated request, so the clock resets while someone is active and only runs out after they go idle. You get most of the security benefit without the mid-checkout logout. It's maybe ten lines: have /api/auth/me and the other authenticated endpoints return a refreshed token, and have the frontend store it.

*Why I asked for this:* The first version kept you signed in for a fixed twelve hours no matter what, so signing in on a library computer left my account open to the next person all day.

**Follow-up 2** *(Claude's suggestion, quoted back to approve it)*

do this recommendation: an absolute cap — put an iat (issued-at) claim in the token and refuse to renew past 12 hours from the original login regardless of activity, so the short idle timeout stays but there is a hard ceiling again.

*Why I asked for this:* After the first change there was no limit on how far the clock could be pushed back, so a stolen login could be kept alive indefinitely with an occasional click.

## Problem 5 - Pydantic AI agent backend

### Initial Prompts

Great, now we will go to Problem 5. The shop chatbot should be built as a PydanticAI agent behind FastAPI, plugged into the front-end chat widget. The API app should be put in backend/main.py - this is the file that you will run with Unvicorn. This agent should be kept as these four files next to it. Backend/prompts/prompt.md is for the system prompt; this same file will be grown later. Backend/agent.py is for the agent entry/wiring. Backend/tools.py is for tools that the agent can call. Backend/models.py is for the pydantic/pydantic AI structured types. In main.py, a chat route should be exposed so that a message from the website returns a reply from the agent (and whatever else is needed for auth/products). For the agent, use gpt-6-luna with my API key that I have given you before. The safety basics and voice of Campus Customs should be put into prompts/prompt.md (the tools and safety will be further expanded upon later). The types in models.py should be started or updated for chat replies / product cards as needed. How the front end talks to FastAPI and how the agent is loaded (model + prompt file) should be noted in output/harness.md. Please ensure that the backend runs from the backend/folder like this: uvicorn main:app --reload --port 8000

### Follow-up Prompt

**Follow-up 1** *(Claude flagged the problem; I asked how to fix it)*

how to fix the unreliability of the reloader in the onedrive folder

*Why I asked for this:* Claude told me the server had been serving old code during the build and needed restarting by hand, which meant I could not trust that what I was testing was what I had saved.

**Follow-up 2** *(Claude's suggestion, quoted back to approve it)*

do this: The one thing I'd call genuinely worth doing is small and isn't a code change: make the reliable command easy to run, so you don't have to remember a long line with a venv path in it. Either a one-line backend/dev.ps1 you double-click, or a campus-customs-backend-dev entry in the project's launch config. Two minutes, zero risk, and your edits start applying automatically again.

*Why I asked for this:* The command that actually worked was long and easy to mistype, so in practice I would have drifted back to the broken one.

## Problem 6 - Tools: product info and stock

### Initial Prompts

Now we will be going to Problem 6. The agent should be given tools that look up real information from campus_customs.db. This information includes product description, price, and how many are in stock (by size when the customer asks). Please make sure that the agent uses the database; no prices or quantities should be invented. If a size is not in stock, just indicate that. The prompts/prompt.md file should be expanded so that the agent knows to call these tools for stock and price questions. Return types should be updated or added in models.py. In output/harness.md, list each tool and provide an explanation regarding which models you chose for lookup results and why.

### Follow-up Prompt

**Follow-up 1** *(Claude flagged the problem; I asked how to fix it)*

how to make sure this failure does not happen again

*The failure: while testing the new lookup tools, one of the test questions died partway through because the server restarted in the middle of answering it, and the connection was cut before any reply came back.*

*Why I asked for this:* A request had been dropped in the middle of a test, and a server that can do that at any moment makes every later result questionable.

## Problem 7 - Chat search that updates the page

### Initial Prompts

Now we will be going to Problem 7. The purpose of this problem is to add a neat feature to the site. When a customer asks about a type of item such as "what hoodies do you have," the agent should search the catalogue and the website should dynamically show those matching items as product cards (short info, price, name, image). Remember that this is an API contract, the agent returns structured product matches and the front end renders them on the website. Once the dynamic product cards are loaded by the new feature, the same single-item page behavior built in Problem 3 should work. So, each product card (including the ones the chat just opened on the page) should open that detail view (full info + large image) when clicked. The prompts/prompt.md file and output/harness.md files should be updated so that it is clear how search results reach the page.

### Follow-up Prompt

**Follow-up 1**

so no issues that need to be resolved for this problem?

*Why I asked for this:* Claude said the feature was finished but had only tried the obvious question, so I wanted it to go looking for problems before I accepted that.

**Follow-up 2**

so now no more bugs for this question?

*Why I asked for this:* The first round of fixes introduced a new fault of its own, which showed that one pass of checking was not enough.

## Problem 8 - Customer memory

### Initial Prompts

Now we will be going to Problem 8. When a shopper is logged in, their chat history should be saved in the database in an appropriate table and it should be reloaded when they return. The agent should know who is chatting (email, name) - put that in agent deps (or a clear pattern that is equivalent) and/or tools that the agent can call. Also sufficient page context should be passed so that if someone is on a product page and asks "do you have this in pink," the agent will know what item they mean. Hint: Code can be put into the agent context. Guests on the site can still chat, but only the history for logged-in users need to persist. How page context is passed, what customer fields that the agent sees, and how user chat history is stored should be documented in output/harness.md

### Follow-up Prompt

**Follow-up 1**

can you check for bugs in this problem

*Why I asked for this:* This problem added the two things most likely to go wrong quietly - saving people's conversations, and telling the chatbot who it is talking to - so I wanted them checked rather than assumed.

**Follow-up 2**

so now no more bugs?

*Why I asked for this:* The first round had fixed the serious fault but not the small one: a refused question was quietly vanishing from the saved conversation while the messages either side of it stayed.

## Problem 9 - Usability Improvements

### Initial Prompts

Now we will be going to Problem 9. Since the core shop now works, we will focus on improving it. First, choose 2 front-end usability improvements and then implement it. Then, choose 2 agent/backend usability improvements and implement it. Things that make the site easier to use and look better are front-end improvements. Things that makes the agent output safer, better, or more accurate are agent/backend improvements. These could be new agent tools or things that make the agent run cheaper or faster. The output/usability.md file should be written either before or as you build. For each of these improvements, specify what you added and why it helps a Campus Customs shopper or business. In the running app, make sure that all the improvements actually show up. Graders will be reading the write-up and look for the features, so do it well.

### Follow-up Prompt

**Follow-up 1**

can you check for bugs in this problem

*Why I asked for this:* The new size filter decides what a shopper sees, and a mistake in it looks like an empty shop rather than an error, so it needed checking before I trusted it.

## Problem 10 - Style the website

### Initial Prompts

Now we will be going to Problem 10. In order to make the site feel like a real Campus Customs storefront, add creative design features with respect to fonts, hierarchy, colors, chat feel, motion, and product presentation. The more innovative and imaginative the design is, the higher the points that I will get. So do this really really really well. In the output/design.md file, give details about what you changed and why it should help customers stick around and buy. This should be short and concrete.

### Follow-up Prompt

**Follow-up 1**

I asked Claude several prompts on improving the visuals of the website. For instance, I frequently asked can "Can you improve the resolution of this xxx product?"

*Why I asked for this:* The design only works if the product photos look right, and they did not: black backgrounds, speckled edges, a few that were the wrong shape, and one jacket with white holes where its hood should be.

## Problem 11 - Site testing (app check)

### Initial Prompts

Now going to Problem 11. The live site should be tested and documented in output/app_check.html (a page that you should be able to double-click to open). Short captions and clear screenshots should be included for 1) chat checking the inventory level of an item (honest price/stock from the DB), 2) dynamic search-result cards appearing after a category question (i.e. hoodies), and 3) one of the visibility features that was used in Problem 9. The HTML should be easy to grade - there should be a heading for each check, screenshot, and 1-2 sentences regarding what the screenshot is proving. The screenshot image files should be put in output/app_check_images/ and they should be linked from app_check.html with relative paths (for instance app_check_images/inventory.png)

### Follow-up Prompt

**Follow-up 1**

any bugs

*Why I asked for this:* The page is meant to be proof that the site works, so a caption claiming something the screenshot did not actually demonstrate would be worse than no caption at all.

**Follow-up 2**

any other bugs

*Why I asked for this:* Asking once had fixed the wording but not the picture - the first screenshot still did not show the stock figure its caption was discussing, because the chat window was sitting on top of it.

## Problem 12 - Audit trail, safety, finish harness

### Initial Prompts

Now going to Problem 12. An append-only output/audit_trail.json of agent-loop activity (time, tool name, stop reason, short args/result) should be kept. It should not be wiped between runs. In prompts/prompt.md, think of some safety rules to give the agent and put them there. Output/harness.md should be finished so that it is clear how the system works. This should have model fields in models.py and why you chose them, tools and abilities, safety rules, and specs (how to run front + back, models, result caps, loop limits).

### Follow-up Prompt

**Follow-up 1**

any bugs

*Why I asked for this:* The whole point of the log is that you can trust it afterwards, so I wanted to know whether it holds up when two shoppers ask something at the same moment.

**Follow-up 2**

any other bugs

*Why I asked for this:* The log was recording the turns that went well and staying silent on the ones that went wrong, which is the opposite of what an audit trail is for.

## Problem 13 - Push to GitHub and submit the URL

### Initial Prompts

Now going to Problem 13. The following items should be in a folder called hw4. AI_prompts.md, requirements.txt, .env.example, .gitiignore, README.md, frontend/, backend/, and output/. Backend/ should include main.py, agent.py, models.py, tools.py, and prompts/. Prompts/ should include prompt.md. The output/ should include harness.md, design.md, usability.md, app_check.html, app_check_images/, and audit_trail.json. Then it should be pushed into a GitHub repository. The repo URL is what I would have to submit and is what the graders will open and clone. Please remember not to put my real .env, campus_customs.db, or product images in the GitHub repo. Use .gitiignore. Include .env.example with only placeholders. Only the local data pack (not in git) should have data/campus_customs.db and data/products/. The agent itself is  4 files under backend/: prompts/prompt.md, agent.py, tools.py, and models.py. The README.md file should explain how to run the front end and back end after the data pack is placed.

### Follow-up Prompt

None was needed
