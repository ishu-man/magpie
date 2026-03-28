import umap
import re
import pandas
import sklearn.cluster as cluster
import plotly.express as px
from sentence_transformers import SentenceTransformer
from app.models import Video
from app.database import select_videos_from_db

# GOAL: perform dimensionality reduction on the embedded video data via UMAP and then apply HDBSCAN clustering on them

MODEL = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def embed_video(embedding_input: str):
    """ Embeds an input string using miniLM """
    embeddings = MODEL.encode(embedding_input)
    return embeddings

def _normalize_description(description: str):
    """
    Strip out URLs and newlines from video descriptions
    """
    trigger_words = [
        "https://",
        "patreon",
    ]
    description += " "
    spaces = []
    for i in range(len(description)):
        if description[i] == '\n':
            spaces.append(i)
    print(spaces)
    words_list = []
    for index in range(len(spaces)):
        if index == 0:
            words_list.append(description[ :spaces[index]])
        elif index == len(spaces) - 1:
            words_list.append(description[spaces[index-1] + 1: ].strip())
        else:
            words_list.append(description[spaces[index-1] + 1: spaces[index]])
    print(words_list)
    normalized_description = ''
    for word in words_list:
        if check_if_trigger_present(trigger_words, word):
            normalized_description += f"{word} "
                
    return normalized_description.strip()
                
        
def check_if_trigger_present(triggers, word):
    for trigger in triggers:
        if word.find(trigger) != -1:
            return False
    return True

def get_hashtags(description: str) -> list[str]:
    hashtags = re.findall(r'#(\w+)', description) # extract hashtags
    return hashtags

def pattern_normalization(description: str) -> str:
    description = re.sub(r'(\d{1,2}:)?\d{1,2}:\d{2}', '', description) # remove timestamps
    description = re.sub(r'[^\w\s]{4,}', '', description) # remove word or space characters more than 3 in length; used for dividers et. al.
    description = re.sub(r'https?://\S+', '', description) # remove specific word https:// till whitespace
    return description

def construct_embedding_input(video: Video) -> str:
    """ Constructs the final embedding input to be fed to all-MiniLM-L6-v2"""
    final_string = ''
    final_string += f'{video.title}' 
    if video.tags:
        final_string += ' '.join(video.tags)
    if video.description:
        final_string += f' {pattern_normalization(video.description)} '
    if video.category:
        final_string += f'{video.category} '
    return final_string.strip()

def perform_clustering(embeddings_list) -> tuple:
    reducer = umap.UMAP(n_components=2)
    reduced = reducer.fit_transform(embeddings_list)

    clusterer = cluster.HDBSCAN(min_cluster_size=10)
    labels = clusterer.fit_predict(reduced)
    return (reduced, labels)

if __name__ == "__main__":
    videos_list = select_videos_from_db()
    embedded_data = []
    titles = []
    for video in videos_list:
       input = construct_embedding_input(video)
       embedded_data.append(embed_video(input))
       titles.append(video.title)
        
    reduced, labels = perform_clustering(embedded_data)
    dataframe = pandas.DataFrame(
        {
        'x': reduced[:, 0],
        'y': reduced[:, 1],
        'cluster': labels.astype(str),
        }
    )
    print("All done.")
    fig = px.scatter(dataframe, x='x', y='y', color='cluster', hover_name=titles, title='Watch later videos')
    fig.show()


