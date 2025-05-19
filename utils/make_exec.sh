# Create a temporary file with the desired content
tempfile=$(mktemp)
echo "#!$(which python)" > "$tempfile"
cat ../main.py >> "$tempfile"

# Move the temporary file to overwrite the original file
mv "$tempfile" ../main.py
# Make the file executable
chmod +x ../main.py