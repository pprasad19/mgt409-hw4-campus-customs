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

*Why I asked for this:* The site kept you logged in for 12 hours no matter what, so if you signed in on a library computer and walked away, the next person could still use your account for the rest of the day. I wanted the site to log you out soon after you stop using it, but not kick you out while you are still shopping.

**Follow-up 2** *(Claude's suggestion, quoted back to approve it)*

do this recommendation: an absolute cap — put an iat (issued-at) claim in the token and refuse to renew past 12 hours from the original login regardless of activity, so the short idle timeout stays but there is a hard ceiling again.

*Why I asked for this:* After the first change, the site pushed your logout time back every time you clicked something, and there was no limit on that. So if someone stole your login, they could keep it working forever just by clicking once in a while. I wanted a firm cutoff so every login ends 12 hours after you signed in, no matter what.

## Problem 5 - Pydantic AI agent backend

### Initial Prompts

Great, now we will go to Problem 5. The shop chatbot should be built as a PydanticAI agent behind FastAPI, plugged into the front-end chat widget. The API app should be put in backend/main.py - this is the file that you will run with Unvicorn. This agent should be kept as these four files next to it. Backend/prompts/prompt.md is for the system prompt; this same file will be grown later. Backend/agent.py is for the agent entry/wiring. Backend/tools.py is for tools that the agent can call. Backend/models.py is for the pydantic/pydantic AI structured types. In main.py, a chat route should be exposed so that a message from the website returns a reply from the agent (and whatever else is needed for auth/products). For the agent, use gpt-6-luna with my API key that I have given you before. The safety basics and voice of Campus Customs should be put into prompts/prompt.md (the tools and safety will be further expanded upon later). The types in models.py should be started or updated for chat replies / product cards as needed. How the front end talks to FastAPI and how the agent is loaded (model + prompt file) should be noted in output/harness.md. Please ensure that the backend runs from the backend/folder like this: uvicorn main:app --reload --port 8000

### Follow-up Prompt

**Follow-up 1** *(Claude flagged the problem; I asked how to fix it)*

how to fix the unreliability of the reloader in the onedrive folder

*Why I asked for this:* When Claude finished Problem 5 it told me the server had been serving old code several times during the build and had to be restarted by hand each time. That meant I could not be sure a change I saved was the one being tested, so I asked how to fix it rather than live with it. Claude's first explanation, that the OneDrive folder was hiding my saved changes from the server, turned out to be wrong. The server does notice every save; what fails is the restart afterwards, which stops the old version halfway and never finishes starting the new one, so the old code keeps answering. That mattered, because the usual cure for folders that sync to the cloud does nothing here - it was tried and made no difference.

**Follow-up 2** *(Claude's suggestion, quoted back to approve it)*

do this: The one thing I'd call genuinely worth doing is small and isn't a code change: make the reliable command easy to run, so you don't have to remember a long line with a venv path in it. Either a one-line backend/dev.ps1 you double-click, or a campus-customs-backend-dev entry in the project's launch config. Two minutes, zero risk, and your edits start applying automatically again.

*Why I asked for this:* The command that actually worked was long and easy to mistype, so in practice I would have forgotten it and gone back to the broken one. Putting it in a small script I can double-click makes the reliable way just as easy as the unreliable way, without changing any of the real code.

## Problem 6 - Tools: product info and stock

### Initial Prompts

Now we will be going to Problem 6. The agent should be given tools that look up real information from campus_customs.db. This information includes product description, price, and how many are in stock (by size when the customer asks). Please make sure that the agent uses the database; no prices or quantities should be invented. If a size is not in stock, just indicate that. The prompts/prompt.md file should be expanded so that the agent knows to call these tools for stock and price questions. Return types should be updated or added in models.py. In output/harness.md, list each tool and provide an explanation regarding which models you chose for lookup results and why.

### Follow-up Prompt

**Follow-up 1** *(Claude flagged the problem; I asked how to fix it)*

how to make sure this failure does not happen again

*The failure: while testing the new lookup tools, one of the test questions died partway through because the server restarted in the middle of answering it, and the connection was cut before any reply came back.*

*Why I asked for this:* Claude told me this was a stray restart rather than a real bug in the shop, but a server that can drop a request at any moment makes every test result questionable, so I wanted it dealt with instead of accepted. It turned out the server was being restarted whenever any file changed, including the wording file for the chatbot, and OneDrive quietly re-saves files about half a minute after I do - which is what triggered it. The server now only restarts when actual program files change. No part of the shop's code was touched; the change was to the small script that starts the server.

## Problem 7 - Chat search that updates the page

### Initial Prompts

Now we will be going to Problem 7. The purpose of this problem is to add a neat feature to the site. When a customer asks about a type of item such as "what hoodies do you have," the agent should search the catalogue and the website should dynamically show those matching items as product cards (short info, price, name, image). Remember that this is an API contract, the agent returns structured product matches and the front end renders them on the website. Once the dynamic product cards are loaded by the new feature, the same single-item page behavior built in Problem 3 should work. So, each product card (including the ones the chat just opened on the page) should open that detail view (full info + large image) when clicked. The prompts/prompt.md file and output/harness.md files should be updated so that it is clear how search results reach the page.

### Follow-up Prompt

**Follow-up 1**

so no issues that need to be resolved for this problem?

*Why I asked for this:* Claude said the feature was finished and working, but it had only tried the obvious question. I wanted it to go looking for problems before I accepted that. It found two. The list of products the chatbot found was being added to the top of the page, so if I had scrolled down at all, the results I just asked for appeared somewhere off the screen where I would never see them. And when the chatbot said something like "we have 27 hoodies, here are eight," there was no way to get to the other nineteen.

**Follow-up 2**

so now no more bugs for this question?

*Why I asked for this:* The fixes from the first round introduced a new problem of their own, which is exactly why I kept asking. The "See all 27" button was built from the words the chatbot used as a heading rather than the words it actually searched for, so a heading like "Yale tailgate gear" sent shoppers to a page with nothing on it. Asking again also turned up that the same product could appear twice in the list of results.

## Problem 8 - Customer memory

### Initial Prompts

Now we will be going to Problem 8. When a shopper is logged in, their chat history should be saved in the database in an appropriate table and it should be reloaded when they return. The agent should know who is chatting (email, name) - put that in agent deps (or a clear pattern that is equivalent) and/or tools that the agent can call. Also sufficient page context should be passed so that if someone is on a product page and asks "do you have this in pink," the agent will know what item they mean. Hint: Code can be put into the agent context. Guests on the site can still chat, but only the history for logged-in users need to persist. How page context is passed, what customer fields that the agent sees, and how user chat history is stored should be documented in output/harness.md

### Follow-up Prompt

**Follow-up 1**

can you check for bugs in this problem

*Why I asked for this:* This problem added the two things most likely to go wrong quietly: saving people's conversations, and telling the chatbot who it is talking to. Asking turned up a security hole. The web address of the page the shopper was on was being handed to the chatbot word for word, so a booby-trapped link could smuggle in its own orders - a link was able to make the assistant end every answer with a word of the attacker's choosing. It now only gets told which kind of page someone is on, chosen from a short fixed list, so a link cannot put words in its mouth.

**Follow-up 2**

so now no more bugs?

*Why I asked for this:* Asking a second time found a smaller gap. When the chatbot refused a question, that exchange was not being saved, so the shopper's question quietly disappeared from their saved conversation while the messages on either side of it stayed. Saved conversations should be a complete record, not one with holes in it.

## Problem 9 - Usability Improvements

### Initial Prompts

Now we will be going to Problem 9. Since the core shop now works, we will focus on improving it. First, choose 2 front-end usability improvements and then implement it. Then, choose 2 agent/backend usability improvements and implement it. Things that make the site easier to use and look better are front-end improvements. Things that makes the agent output safer, better, or more accurate are agent/backend improvements. These could be new agent tools or things that make the agent run cheaper or faster. The output/usability.md file should be written either before or as you build. For each of these improvements, specify what you added and why it helps a Campus Customs shopper or business. In the running app, make sure that all the improvements actually show up. Graders will be reading the write-up and look for the features, so do it well.

### Follow-up Prompt

**Follow-up 1**

can you check for bugs in this problem

*Why I asked for this:* The new size filter was the part most likely to go wrong quietly, because it decides what a shopper sees and a mistake just looks like an empty shop rather than an error. Asking turned one up. The filter has an "Any" button meaning "do not filter", and clicking it worked, but the shop had not been taught that "Any" is not a real size. So anyone opening a shared or typed-out link with that setting in it saw a catalogue with nothing in it at all. It now treats "Any" as no filter, and real sizes still work.

## Problem 10 - Style the website

### Initial Prompts

Now we will be going to Problem 10. In order to make the site feel like a real Campus Customs storefront, add creative design features with respect to fonts, hierarchy, colors, chat feel, motion, and product presentation. The more innovative and imaginative the design is, the higher the points that I will get. So do this really really really well. In the output/design.md file, give details about what you changed and why it should help customers stick around and buy. This should be short and concrete.

### Follow-up Prompt

**Follow-up 1**

I asked Claude several prompts on improving the visuals of the website. For instance, I frequently asked can "Can you improve the resolution of this xxx product?"

*Why I asked for this:* The design work only lands if the product photos look right, and they did not. Most of them had come on a black background, which looked like a mistake next to white product cards, and the ones that had been cleaned up still had problems I could see on the page: a crust of dark speckle around the edges, jagged outlines, a few photos that were the wrong shape and left grey stripes down the sides of their card, and one jacket with white holes where its hood should be. So I kept pointing at specific products and asking for them to be fixed. Each round found a different cause rather than the same one, and a few of the fixes had to be thrown out after they turned out to be quietly damaging the clothes - erasing the small print on a t-shirt, or chewing notches out of a sleeve - which is why it took several passes to get right.

## Problem 11 - Site testing (app check)

### Initial Prompts

Now going to Problem 11. The live site should be tested and documented in output/app_check.html (a page that you should be able to double-click to open). Short captions and clear screenshots should be included for 1) chat checking the inventory level of an item (honest price/stock from the DB), 2) dynamic search-result cards appearing after a category question (i.e. hoodies), and 3) one of the visibility features that was used in Problem 9. The HTML should be easy to grade - there should be a heading for each check, screenshot, and 1-2 sentences regarding what the screenshot is proving. The screenshot image files should be put in output/app_check_images/ and they should be linked from app_check.html with relative paths (for instance app_check_images/inventory.png)

### Follow-up Prompt

**Follow-up 1**

any bugs

*Why I asked for this:* The page is meant to be proof that the site works, so a
claim on it that is not actually backed up is worse than no claim at all. This
caught two. The caption said the stock number came from the database rather than
the chatbot making it up, but nothing on the page showed that, so Claude tested
it by asking about a second product and got back the exact pattern of sold-out
and in-stock sizes, which cannot be guessed. The caption also said the assistant
"cannot invent" stock, which is stronger than anyone can promise about a
chatbot, so it now says it looks the numbers up instead.

**Follow-up 2**

any other bugs

*Why I asked for this:* The first screenshot did not show what its caption said
it showed. I had asked the chat about XL, and the answer was right, but the chat
window was sitting on top of the XL figure on the page behind it - so the one
number being discussed was hidden. Asking about XS instead fixed it, because
that part of the page stays visible, and now the question, the answer, the
price and the stock count are all in the same picture. It proves itself rather
than asking the grader to take my word for it.

## Problem 12 - Audit trail, safety, finish harness

### Initial Prompts

Now going to Problem 12. An append-only output/audit_trail.json of agent-loop activity (time, tool name, stop reason, short args/result) should be kept. It should not be wiped between runs. In prompts/prompt.md, think of some safety rules to give the agent and put them there. Output/harness.md should be finished so that it is clear how the system works. This should have model fields in models.py and why you chose them, tools and abilities, safety rules, and specs (how to run front + back, models, result caps, loop limits).

### Follow-up Prompt

**Follow-up 1**

any bugs

*Why I asked for this:* The whole point of the log is that you can trust it
later, so it was worth checking it holds up when the shop is busy. It did not.
Writing 300 records at once kept only 272 of them and left 5 broken blank lines
- so if two shoppers asked a question at the same moment, one of their records
could simply disappear. That is the worst way for an audit log to fail, because
you would never know a line was missing. Claude made the writes take turns, and
the same test now keeps all 300. This also turned up a separate problem in the
search that I have left alone for now: asking for a "navy hoodie" returns 82
products because it matches either word, and only 27 of them are hoodies.

**Follow-up 2**

any other bugs

*Why I asked for this:* The log was recording the turns that went fine and
staying silent on the ones that went wrong. If the provider blocked a message -
which is what happens when somebody tries to jailbreak the chatbot - nothing was
written down at all. That is exactly the event you would want a record of, and
it was invisible. It now records every failed turn with the reason. Asking twice
was worth it: the first answer I got said the tool logging had been checked, and
when Claude went to actually prove it, the test it had relied on turned out to
pass without testing anything.

## Problem 13 - Push to GitHub and submit the URL

### Initial Prompts

Now going to Problem 13. The following items should be in a folder called hw4. AI_prompts.md, requirements.txt, .env.example, .gitiignore, README.md, frontend/, backend/, and output/. Backend/ should include main.py, agent.py, models.py, tools.py, and prompts/. Prompts/ should include prompt.md. The output/ should include harness.md, design.md, usability.md, app_check.html, app_check_images/, and audit_trail.json. Then it should be pushed into a GitHub repository. The repo URL is what I would have to submit and is what the graders will open and clone. Please remember not to put my real .env, campus_customs.db, or product images in the GitHub repo. Use .gitiignore. Include .env.example with only placeholders. Only the local data pack (not in git) should have data/campus_customs.db and data/products/. The agent itself is  4 files under backend/: prompts/prompt.md, agent.py, tools.py, and models.py. The README.md file should explain how to run the front end and back end after the data pack is placed.

### Follow-up Prompt

