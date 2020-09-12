#! /usr/bin/env python3
# coding: utf-8
# Copyright (c) oatsu
"""
歌唱DBをUTAU音源化する
wavファイルと同じディレクトリにoto.iniを生成する。
"""
import json
import os
from glob import glob
from pprint import pprint

import utaupy as up

PATH_CONFIG_JSON = 'config.json'
# CONSONANTS = ['b', 'by', 'ch', 'd', 'dy', 'f', 'g', 'gy', 'h', 'hy', 'j',
#               'k', 'ky', 'm', 'my', 'n', 'ny', 'p', 'py', 'r', 'ry', 's',
#               'sh', 't', 'ts', 'ty', 'v', 'w', 'y', 'z']
# VOWELS = ['a', 'i', 'u', 'e', 'o', 'N']
# VOWELS = ['a', 'i', 'u', 'e', 'o', 'N', 'cl']


def label2otoini_for_utau(label, name_wav, dict_config, dt=100, threshold=300):
    """
    LabelオブジェクトをOtoIniオブジェクトに変換
    UTAU音源として使えるようにチューニングする。

    |   dt      |     子音      |   dt    |  残りの母音   |
    |左ブランク |オーバーラップ |先行発声 |子音部固定範囲 |右ブランク
    """
    # config を展開
    dict_roma2kana = dict_config['roma2kana']
    consonants = dict_config['phoneme_category']['consonants']
    vowels = dict_config['phoneme_category']['vowels']
    # time_order_ratio = label_time_order / otoini_time_order
    time_order_ratio = 10**(-4)

    l = []  # Otoオブジェクトを格納するリスト
    phonemes = label.values

    # ラベルの各PhoenmeオブジェクトをOtoオブジェクトに変換して、リストにまとめる。
    tmp = []
    prev_vowel = '-'
    for phoneme in phonemes:
        if phoneme.symbol in consonants:
            tmp.append(phoneme)
        elif phoneme.symbol in vowels:
            if time_order_ratio * (phoneme.end - phoneme.start) > threshold:
                tmp.append(phoneme)
                oto = up.otoini.Oto()
                oto.filename = name_wav
                try:
                    kana = dict_roma2kana[''.join([ph.symbol for ph in tmp])][0]
                    oto.alias = '{} {}'.format(prev_vowel, kana)
                    # oto.alias = '{}'.format(''.join([ph.symbol for ph in tmp]))
                    oto.offset = (time_order_ratio * tmp[0].start) - dt
                    oto.overlap = dt
                    oto.preutterance = (time_order_ratio * tmp[-1].start) - oto.offset
                    oto.consonant = oto.preutterance + dt
                    oto.cutoff2 = time_order_ratio * tmp[-1].end - dt
                    l.append(oto)
                except KeyError as err:
                    print('[ERROR]:', err)
            tmp = []
            prev_vowel = phoneme.symbol.replace('N', 'n')
        else:
            tmp = []
            prev_vowel = '-'

    # Otoiniオブジェクト化
    otoini = up.otoini.OtoIni()
    otoini.values = l
    return otoini


def main():
    """
    パラメータとパスを指定して実行
    """
    # 設定ファイルを読み取り
    with open(PATH_CONFIG_JSON) as fj:
        d_config = json.load(fj)

    # ラベルファイルがあるフォルダのパスを入力
    path_labdir = input('path_labdir: ')
    # 左ブランクとかのずらす長さ
    dt = float(input('dt_shift [ms] (100くらい): '))
    labfiles = glob(f'{path_labdir}/**/*.lab', recursive=True)
    pprint(labfiles)

    # 変換開始
    otoini = up.otoini.OtoIni()
    for path_lab in labfiles:
        basename_wav = os.path.basename(path_lab).replace('.lab', '.wav')
        label = up.label.load(path_lab)
        otoini += label2otoini_for_utau(label, basename_wav, d_config, dt=dt)
    total_otoini = up.otoini.OtoIni()
    # 変換終了
    print('登録エイリアス数:', len(total_otoini.values))
    # ファイル出力
    total_otoini.write(path_labdir + '/oto.ini')


if __name__ == '__main__':
    main()
    print()
    input('Press Enter to exit')
