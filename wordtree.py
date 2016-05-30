from string import Template


def get_word_tree_html(json_formatted, root_word, lowercase=True, tree_type='double'):
    """
        Generates HTML that will draw a word tree using the Google visualization API when rendered.

        See https://developers.google.com/chart/interactive/docs/gallery/wordtree for further details.

    Args:
        json_formatted: JSON to pass directly to the google data visualization API
        root_word: the word to use as the root of the tree
        lowercase: if true, lowercase the passed texts
        tree_type: the type of word tree, double, suffix, or prefix

    Returns:
        HTML that will draw a word tree using the Google visualization API when rendered
    """

    with open('wordtree_template.html', 'r') as my_file:
        html_template = Template(my_file.read())
    return html_template.substitute(root_word=root_word,
                                    tree_type=tree_type,
                                    json_formatted=json_formatted.lower() if lowercase else json_formatted)
