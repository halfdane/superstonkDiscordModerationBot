import logging
import re

import yaml
from nltk import word_tokenize
from nltk.stem import WordNetLemmatizer

import disnake
from disnake.ext import commands

import discordReaction
from helper.redditor_history import redditor_history


class LemmaTokenizer:
    def __init__(self):
        self.stop_words = ENGLISH_STOP_WORDS.union(SUPERSTONK_STOP_WORDS)
        self.wnl = WordNetLemmatizer()

    def __call__(self, doc):
        return [self.wnl.lemmatize(t) for t in word_tokenize(doc) if
                (t.isalpha() and len(t) > 2) and t not in self.stop_words]


class Hanami(commands.Cog):

    def __init__(self, subreddit=None, config=None, bot=None):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.subreddit = subreddit
        self.bot = bot
        self.hanami_configs = re.compile(r'hanami_config/(.+)')
        self.tokenizer = LemmaTokenizer()
        self.config = config
        if config is not None:
            self.preprocess_config()
        self.test_config = True

    async def on_ready(self):
        if self.subreddit is None:
            self.subreddit = self.bot.subreddit

        self.config = await self.load_config()
        self.preprocess_config()

    async def load_config(self):
        config = dict()
        config['types'] = dict()

        if not self.test_config:
            print(f"iterating {self.subreddit.wiki}")
            async for wikipage in self.subreddit.wiki:
                print(f"handling {wikipage}")
                await wikipage.load()
                if hanami_config := self.hanami_configs.match(wikipage.name):
                    self._logger.info(f"Reading {self.subreddit} {wikipage.name}")
                    wiki_config = yaml.safe_load(wikipage.content_md)
                    config['types'][hanami_config.group(1)] = wiki_config
                else:
                    self._logger.info(f"Ignoring {self.subreddit} {wikipage.name}")
        else:
            self._logger.info(f"Reading {self.subreddit} hanami_config/testing")
            wikipage = await self.subreddit.wiki.get_page("hanami_config/testing")
            wiki_config = yaml.safe_load(wikipage.content_md)
            config['types']['testing'] = wiki_config

        return config

    def preprocess_config(self):
        for name, a_type in self.config['types'].items():
            a_type['keywords'] = {re.compile(k): v for k, v in a_type['keywords'].items()}

    def preprocess_phrase(self, phrase):
        return " ".join(self.tokenizer(phrase))

    def categorize(self, phrase):
        categories = dict()
        for name, a_type in self.config['types'].items():
            for trigger, weight in a_type['keywords'].items():
                if trigger.search(phrase):
                    current = categories.get(name, 0)
                    categories[name] = current + weight

        return categories

    @commands.slash_command(description="drop the config")
    async def hanami(self, ctx, *, redditor):
        embed = disnake.Embed(title=f"Information about ``{ctx.guild}``",
                              description='henlo world', color=0xf7fcfd)
        await ctx.send(embed=embed)


    #
    # @hanami.sub_command(description="drop the config")
    # async def config(self, ctx, *, redditor):
    #     pass
    #
    # @hanami.sub_command(description="drop the config")
    # async def whatever(self, ctx):
    #     embed = disnake.Embed(title=f"Information about ``{ctx.guild}``",
    #                           description='henlo world', color=0xf7fcfd)
    #     await ctx.send(embed=embed)






SUPERSTONK_STOP_WORDS = ("com", "www", "https", "reddit", "hi", "just",
                         "ss", "utm_source", "utm_medium", "hey", "nbsp", "iossmf", "ios_app",
                         "android_app", "guys", "superstonk", 'share')

ENGLISH_STOP_WORDS = frozenset([
    "a", "about", "above", "across", "after", "afterwards", "again", "against",
    "all", "almost", "alone", "along", "already", "also", "although", "always",
    "am", "among", "amongst", "amoungst", "amount", "an", "and", "another",
    "any", "anyhow", "anyone", "anything", "anyway", "anywhere", "are",
    "around", "as", "at", "back", "be", "became", "because", "become",
    "becomes", "becoming", "been", "before", "beforehand", "behind", "being",
    "below", "beside", "besides", "between", "beyond", "bill", "both",
    "bottom", "but", "by", "call", "can", "cannot", "cant", "co", "con",
    "could", "couldnt", "cry", "de", "describe", "detail", "do", "done",
    "down", "due", "during", "each", "eg", "eight", "either", "eleven", "else",
    "elsewhere", "empty", "enough", "etc", "even", "ever", "every", "everyone",
    "everything", "everywhere", "except", "few", "fifteen", "fifty", "fill",
    "find", "fire", "first", "five", "for", "former", "formerly", "forty",
    "found", "four", "from", "front", "full", "further", "get", "give", "go",
    "had", "has", "hasnt", "have", "he", "hence", "her", "here", "hereafter",
    "hereby", "herein", "hereupon", "hers", "herself", "him", "himself", "his",
    "how", "however", "hundred", "i", "ie", "if", "in", "inc", "indeed",
    "interest", "into", "is", "it", "its", "itself", "keep", "last", "latter",
    "latterly", "least", "less", "ltd", "made", "many", "may", "me",
    "meanwhile", "might", "mill", "mine", "more", "moreover", "most", "mostly",
    "move", "much", "must", "my", "myself", "name", "namely", "neither",
    "never", "nevertheless", "next", "nine", "no", "nobody", "none", "noone",
    "nor", "not", "nothing", "now", "nowhere", "of", "off", "often", "on",
    "once", "one", "only", "onto", "or", "other", "others", "otherwise", "our",
    "ours", "ourselves", "out", "over", "own", "part", "per", "perhaps",
    "please", "put", "rather", "re", "same", "see", "seem", "seemed",
    "seeming", "seems", "serious", "several", "she", "should", "show", "side",
    "since", "sincere", "six", "sixty", "so", "some", "somehow", "someone",
    "something", "sometime", "sometimes", "somewhere", "still", "such",
    "system", "take", "ten", "than", "that", "the", "their", "them",
    "themselves", "then", "thence", "there", "thereafter", "thereby",
    "therefore", "therein", "thereupon", "these", "they", "thick", "thin",
    "third", "this", "those", "though", "three", "through", "throughout",
    "thru", "thus", "to", "together", "too", "top", "toward", "towards",
    "twelve", "twenty", "two", "un", "under", "until", "up", "upon", "us",
    "very", "via", "was", "we", "well", "were", "what", "whatever", "when",
    "whence", "whenever", "where", "whereafter", "whereas", "whereby",
    "wherein", "whereupon", "wherever", "whether", "which", "while", "whither",
    "who", "whoever", "whole", "whom", "whose", "why", "will", "with",
    "within", "without", "would", "yet", "you", "your", "yours", "yourself",
    "yourselves"])
