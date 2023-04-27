import pymorphy2
import re
from data.history import History
from data import db_session

morph = pymorphy2.MorphAnalyzer()

parts_of_speech = {'NOUN': 'Имя существительное',
                   'ADJF': 'Имя прилагательное',
                   'ADJS': 'Краткое прилагательное',
                   'COMP': 'Сравнительное прилагательное',
                   'VERB': 'Глагол',
                   'INFN': 'Глагол в начальной форме',
                   'PRTF': 'Причастие',
                   'PRTS': 'Краткое причастие',
                   'GRND': 'Деепричастие',
                   'NUMR': 'Имя числительное',
                   'ADVB': 'Наречие',
                   'PRED': 'Наречие',
                   'NPRO': 'Местоимение',
                   'PREP': 'Предлог',
                   'CONJ': 'Союз',
                   'PRCL': 'Частица',
                   'INTJ': 'Междометие'}

cases = {'nomn': 'Именительный',
         'gent': 'Родительный',
         'datv': 'Дательный',
         'accs': 'Винительный',
         'ablt': 'Творительный',
         'loct': 'Предложный',
         'voct': 'Звательный',
         'gen2': 'Второй родительный',
         'acc2': 'Второй винительный',
         'loc2': 'Второй предложный'}

nums = {'sing': 'Единственное',
        'plur': 'Множественное'}

genders = {'masc': 'Мужской',
           'femn': 'Женский',
           'neut': 'Средний'}

anims = {'anim': 'Одушевлённое',
         'inan': 'Неодушевлённое'}

moods = {'indc': 'Изъявительное',
         'impr': 'Повелительное'}

types_ADJF = {'Qual': 'Качественное',
              'Apro': 'Местоименное',
              'Anum': 'Порядковое',
              'Poss': 'Притяжательное'}

persons = {'1per': 'Первое',
           '2per': 'Второе',
           '3per': 'Третье'}

tenses = {'pres': 'Настоящее',
          'past': 'Прошедшее',
          'futr': 'Будущее'}

transitivities = {'tran': 'Переходный',
                  'intr': 'Непереходный'}

aspects = {'perf': 'Совершенный',
           'impf': 'Несовершенный'}

voices = {'actv': 'Действительный',
          'pssv': 'Страдательный'}


def make_note(message):  # создание записи в БД
    hist = History()
    hist.tg_id = message.from_user.id
    hist.request = message.text
    db_sess = db_session.create_session()
    db_sess.add(hist)
    db_sess.commit()


def is_russian(word):  # проверка на допустимые символы в русских словах
    alph = [i for i in range(1040, 1104)] + [1105, 1025, 45]
    flag = True
    for sym in word:
        if ord(sym) not in alph:
            flag = False
    return flag


def declensioning(word, part, gender):
    if part != 'Имя существительное':
        return None
    else:
        if word in ['бремя', 'время', 'вымя', 'знамя', 'имя',
                    'пламя', 'племя', 'семя', 'стремя', 'темя', 'путь']:
            return 'Разносклоняемое'
        elif (gender in ['Мужской', 'Женский'] and word[-1] in ['а', 'я']) or gender == 'Общий':
            return 'Первое'
        elif gender in ['Мужской', 'Средний']:
            return 'Второе'
        else:
            return 'Третье'


def conjugationing(word, part):
    if part in ['Глагол', 'Глагол в начальной форме']:
        exceptins_1 = ['брить', 'стелить', 'зиждиться']
        exceptions_2 = ['гнать', 'держать', 'дышать', 'обидеть', 'слышать', 'видеть',
                        'ненавидеть', 'терпеть', 'смотреть', 'вертеть', 'зависеть']
        if word in exceptins_1:
            return 'Первое'
        elif word in exceptions_2 or word + 'ся' in exceptions_2 or word[-3] == 'ить':
            return 'Второе'
        else:
            return 'Первое'
    else:
        return None


def recurrencing(word, part):
    if part in ['Глагол', 'Глагол в начальной форме']:
        if word[-2:] in ['сь', 'cя']:
            return 'Возвратный'
        else:
            return 'Невозвратный'
    elif part in ['Причастие', 'Деепричастие']:
        if word[-2:] in ['сь', 'cя']:
            return 'Возвратное'
        else:
            return 'Невозвратное'
    else:
        return None


def morphying(message):
    reply_variants = []
    for variant in range(len(morph.parse(message.text))):
        if str(morph.parse(message.text)[variant][4][0][0]) == 'FakeDictionary()':
            continue
        slovo = morph.parse(message.text)[variant].tag
        part_of_speech = parts_of_speech.get(str(slovo.POS))  # часть речи
        if part_of_speech in ['Причастие', 'Деепричастие']:
            normal_form = morph.parse(message.text)[variant].inflect({'sing', 'nomn'}).word
        else:
            normal_form = morph.parse(message.text)[variant].normal_form
        case = cases.get(str(slovo.case))  # падеж
        num = nums.get(str(slovo.number))  # число
        tens = tenses.get(str(slovo.tense))  # время
        gender = None  # род
        if 'ms-f' in str(slovo):
            gender = 'Общий'
        else:
            gender = genders.get(str(slovo.gender))
        voice = voices.get(str(slovo.voice))  # залог
        anim = anims.get(str(slovo.animacy))  # одушевленность
        mood = moods.get(str(slovo.mood))  # наклонение
        person = persons.get(str(slovo.person))  # лицо
        declension = declensioning(str(morph.parse(message.text)[variant].normal_form), part_of_speech,
                                   gender)  # склонение
        transitivity = transitivities.get(str(slovo.transitivity))  # переходность
        recurrence = recurrencing(message.text, part_of_speech)  # возвратность
        aspect = aspects.get(str(slovo.aspect))  # вид
        conjugation = conjugationing(morph.parse(message.text)[variant].normal_form, part_of_speech)  # спряжение

        razbor = {'Начальная форма слова: ': normal_form, 'Часть речи: ': part_of_speech, 'Залог': voice,
                  'Склонение: ': declension, 'Cпряжение: ': conjugation,
                  'Переходность: ': transitivity, 'Вид: ': aspect, 'Одушевленность: ': anim,
                  'Время: ': tens, 'Род: ': gender, 'Падеж: ': case, 'Наклонение: ': mood,
                  'Лицо: ': person, 'Число: ': num, 'Возвратность: ': recurrence}
        razbor = {key: value for key, value in razbor.items() if value is not None}
        razbor = [[key, value] for key, value in razbor.items()]
        reply = []
        for i in range(len(razbor)):
            reply.append(''.join(razbor[i]))
        reply_variants.append('\n'.join(reply))
    if len(reply_variants) == 0:
        return ['Вероятно, в слове допущена ошибка']
    return reply_variants


def analyzying(file):
    otvet = {'NOUN': 0, 'ADJF': 0, 'ADJS': 0, 'COMP': 0, 'VERB': 0, 'INFN': 0, 'PRTF': 0, 'PRTS': 0, 'GRND': 0,
             'NUMR': 0, 'ADVB': 0, 'PRED': 0, 'NPRO': 0, 'PREP': 0, 'CONJ': 0, 'PRCL': 0, 'INTJ': 0, 'None': 0}
    for stroka in file:
        slova = re.sub(r'[^\w\s-]', ' ', stroka).split()
        slova = [x for x in slova if is_russian(x)]
        for slovo in slova:
            if str(morph.parse(slovo)[0][4][0][0]) != 'FakeDictionary()':
                otvet[str(morph.parse(slovo)[0].tag.POS)] += 1

    reply = {'Имён существительных': otvet['NOUN'],
             'Имён прилагательных': otvet['ADJF'] + otvet['ADJS'] + otvet['COMP'],
             'Глаголов': otvet['VERB'] + otvet['INFN'],
             'Причастий': otvet['PRTF'] + otvet['PRTS'],
             'Деепричастий': otvet['GRND'],
             'Имён числительных': otvet['NUMR'],
             'Наречий': otvet['ADVB'] + otvet['PRED'],
             'Местоимений': otvet['NPRO'],
             'Предлогов': otvet['PREP'],
             'Союзов': otvet['CONJ'],
             'Частиц': otvet['PRCL'],
             'Междометий': otvet['INTJ']}
    reply = {key: value for key, value in reply.items() if value != 0}
    if len(reply) != 0:
        reply = [[key, str(value)] for key, value in reply.items()]
        otvet = []
        for i in range(len(reply)):
            otvet.append(': '.join(reply[i]))
        return '\n'.join(otvet)
    else:
        return 'Текст неподдерживаемого формата или является нечитаемым'
