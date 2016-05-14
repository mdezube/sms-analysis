def get_word_tree_html(json_formatted_for_wordtree, root_word, lowercase=True, tree_type='double'):
    """
        Generates HTML that will draw a word tree using the Google visualization API when rendered.

        See https://developers.google.com/chart/interactive/docs/gallery/wordtree for further details.

    Args:
        json_formatted_for_wordtree: JSON to pass directly to the google data visualization API
        root_word: the word to use as the root of the tree
        lowercase: if true, lowercase the passed texts
        tree_type: the type of word tree, double, suffix, or prefix

    Returns:
        HTML that will draw a word tree using the Google visualization API when rendered
    """
    html_blob = """
    <html>
      <head>
        <script type="text/javascript">
            var chart;
            var data;
            var options = {
                wordtree: {
                  format: 'implicit',
                  word: '%s',
                  type: '%s',
                }
            };

            function initChart() {
                data = google.visualization.arrayToDataTable(%s);
                chart = new google.visualization.WordTree(document.getElementById('wordtree_basic'));
            }

            function drawChart() {
                chart.draw(data, options);
            }

            function setRootWordFromForm() {
                options.wordtree.word = document.getElementById('root_word').value;
                drawChart();
            }

            // Is it the first time we're being loaded?
            if (typeof(google) == 'undefined') {
                var script = document.createElement('script');
                script.src = 'https://www.gstatic.com/charts/loader.js';
                var head = document.getElementsByTagName('head')[0];
                script.onload  = function() {
                    google.charts.load('current', {packages:['wordtree']});
                    google.charts.setOnLoadCallback(function() {
                        initChart();
                        drawChart();
                    });
                    head.removeChild(script);
                };
                head.appendChild(script);
            } else {
                initChart();
                drawChart();
            }
        </script>
      </head>
      <body>
        Root Word: <input type="text" id="root_word" value="%s">
        <button type="button" onclick="setRootWordFromForm()">Update Tree</button>
        <br>
        <div id="wordtree_basic" style="width: 900px; height: 600px;"></div>
      </body>
    </html>
    """
    return html_blob % (root_word,
                        tree_type,
                        json_formatted_for_wordtree.lower() if lowercase else json_formatted_for_wordtree,
                        root_word)
