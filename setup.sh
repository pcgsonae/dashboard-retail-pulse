mkdir -p ~/.streamlit/
echo "\
[server]\n\
headless = true\n\
port = $PORT\n\
enableCORS = false\n\
\n\
[theme]\n\
primaryColor='#000f68'\n\
backgroundColor='#f0f0eb'\n\
secondaryBackgroundColor='#99C7FF'\n\
textColor='#000f68'\n\
font = 'sans serif'\n\
\n\
" > ~/.streamlit/config.toml
