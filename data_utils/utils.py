import sys
import os
import operator
from nltk.translate.bleu_score import sentence_bleu
import json
import zipfile
import string
import Queue
import numpy as np
from nlgeval import NLGEval
from nlgeval import compute_metrics
from fuzzysearch import find_near_matches



project_dir = "/scratch/home/zhiyu/wiki2bio/"
model_dir = project_dir + "results/res/pointer-gen/loads/33/"
#model_dir = "/scratch/home/zhiyu/wiki2bio_ori/results/res/faget/1548416477366/loads/32/"

train_table = project_dir + "original_data/train.box"
test_table = project_dir + "original_data/test.box"
summary_gold_in = project_dir + "original_data/test.summary"

summary_ours_in = model_dir + "test_summary_copy.clean.txt"
summary_with_unk = model_dir + "test_summary_copy.txt"

### evaluate
cider_in = project_dir + "cider/results-baseline.json"

file_out = project_dir + "data_misc/test_compare_error_cider_1.0_baseline.txt"

def gen_compare(cider_in, table_in, summary_ours_in, summary_with_unk, summary_gold_in, file_out):
	'''
	gen file for error case compare
	'''

	with open(table_in) as f:
		table = f.readlines()

	with open(summary_ours_in) as f:
		res_ours = f.readlines()

	with open(summary_with_unk) as f:
		res_ours_unk = f.readlines()

	with open(summary_gold_in) as f:
		res_gold = f.readlines()

	with open(cider_in) as f:
		res_cider = json.load(f)
		score_cider = res_cider["CIDEr"]
		score_cider_d = res_cider["CIDErD"]

		print len(score_cider_d)

	nlgeval = NLGEval()

	out = open(file_out, "w")
	i = 0
	num_write = 0
	avg_len_right = 0.0
	avg_len_wrong = 0.0

	for this_cider, this_box, this_ours, this_unk, this_gold in zip(score_cider_d, table, res_ours, res_ours_unk, res_gold):

		references = [this_gold.strip().split()]
		hypothesis = this_ours.strip().split()
		this_bleu = sentence_bleu(references, hypothesis)
		this_cider = float(this_cider)
		metrics_dict = nlgeval.compute_individual_metrics([this_gold.strip()], this_ours.strip())
		this_meteor = metrics_dict["meteor"]

		i += 1

		#if this_bleu < 0.1:
		#if this_bleu > 0.1 and this_bleu < 0.2:
		#if this_bleu > 0.2 and this_bleu < 0.3:
		if this_cider < 1.0:

			avg_len_wrong += len(this_box.strip().split("\t"))
			num_write += 1
			out.write("########## Test " + str(i) +  " ##########\n")

			for each_token in this_box.strip().split("\t"):
				out.write(each_token + "\n")

			out.write("########## Gold ##########\n")
			out.write(this_gold.strip() + "\n")
			out.write("########## Ours ##########\n")
			out.write(this_ours.strip() + "\n")
			out.write("########## Ours with unk ##########\n")
			out.write(this_unk.strip() + "\n")
			out.write("########## bleu ##########\n")
			out.write(str(this_bleu) + "\n")
			out.write("########## cider-d ##########\n")
			out.write(str(this_cider) + "\n")
			out.write("########## meteor ##########\n")
			out.write(str(this_meteor) + "\n")
			out.write("\n")

		else:
			avg_len_right += len(this_box.strip().split("\t"))


	out.close()

	print "All: ", i
	print "Write: ", num_write

	print "avg_len_wrong: ", float(avg_len_wrong) / num_write
	print "avg_len_right: ", float(avg_len_right) / (i - num_write)



def check_field(table_in, field_name):


	with open(table_in) as f:
		table = f.readlines()

	num_all = 0
	num_target = 0

	for this_box in table:

		num_all += 1

		for each_token in this_box.strip().split("\t"):

			if each_token.split(":")[0].split("_")[0] == field_name:
				num_target += 1
				break



	print "All: ", num_all
	print "Target: ", num_target
	print float(num_target) / num_all


def gen_cider_input(file_in, file_out):
	'''
	generate json file for cider
	[{"image_id": "2008_006488.jpg", "caption": "Man in a boat fishing."}, 
	'''

	with open(file_in) as f:
		res = f.readlines()

	data = []

	for ind, this_line in enumerate(res):
		this_data = {}
		this_data["image_id"] = str(ind)
		this_data["caption"] = this_line.strip().decode('utf-8').encode('utf-8')
		data.append(this_data)

	with open(file_out, "w") as f:
		f.write(json.dumps(data))

	print ind



def merge_value_field_vocab(word_vocab_file, field_vocab_file, merge_vocab):
	'''
	merge word vocab with field vocab
	'''


	word_vocab = {}
	field_vocab = {}

	with open(word_vocab_file) as f:
		for line in f:
			line_list = line.strip().split("\t")
			word_vocab[line_list[0]] = int(line_list[1])

	with open(field_vocab_file) as f:
		for line in f:
			line_list = line.strip().split("\t")
			for each_word in line_list[0].split("_"):
				if each_word.strip() != "" and each_word not in word_vocab:
					word_vocab[each_word] = -1


	with open(merge_vocab, "w") as f:
		for tmp in word_vocab:
			f.write(tmp + "\t" + str(1) + "\n")

	print "All: ", len(word_vocab)


def add_vocab(origianl_vocab, add_vocab, out_vocab):
	'''
	extend vocab
	'''

	word_vocab = {}

	with open(origianl_vocab) as f:
		for line in f:
			line_list = line.strip().split("\t")
			if len(line_list) > 1:
				word_vocab[line_list[0]] = int(line_list[1])

	with open(add_vocab) as f:
		for line in f:
			line_list = line.strip().split("\t")
			if line_list[0] != "" and line_list[0] not in word_vocab:
				word_vocab[line_list[0]] = -1


	ind = 0
	with open(out_vocab, "w") as f:
		for tmp in word_vocab:
			f.write(tmp + "\t" + str(ind) + "\n")
			ind += 1

	print "All: ", len(word_vocab)




def create_ori_vocab(in_box, in_summary, word_vocab_file, field_vocab_file, size):
	'''
	create original vocab for each domain
	field: 2000
	word: 20000
	'''

	word_vocab = {}
	field_vocab = {}

	with open(in_box) as f:
		for line in f:
			for each_item in line.strip("\n").split("\t"):

				this_field_name = "_".join(each_item.split(":")[0].split("_")[:-1])
				if this_field_name not in field_vocab:
					field_vocab[this_field_name] = 0
				field_vocab[this_field_name] += 1

				this_value_token = each_item.split(":")[1]
				if this_value_token.isdigit():
					continue
				if this_value_token not in word_vocab:
					word_vocab[this_value_token] = 0
				word_vocab[this_value_token] += 1



	with open(in_summary) as f:
		for line in f:
			for token in line.strip().split(" "):
				if token.isdigit():
					continue
				if token not in word_vocab:
					word_vocab[token] = 0
				word_vocab[token] += 1


	sorted_word = sorted(word_vocab.items(), key=operator.itemgetter(1), reverse=True)
	sorted_field = sorted(field_vocab.items(), key=operator.itemgetter(1), reverse=True)

	print "All words: ", len(sorted_word)
	print "All fields: ", len(sorted_field)

	sorted_word = sorted_word[0:size]


	with open(word_vocab_file, "w") as f:
		for item in sorted_word:
			f.write(item[0] + "\t" + str(item[1]) + "\n")

	with open(field_vocab_file, "w") as f:
		for item in sorted_field:
			f.write(item[0] + "\t" + str(item[1]) + "\n")


def extract_glove_vocab(file_in, file_out):
	'''
	extract vocab from glove embedding
	'''

	ind = 0
	f_out = open(file_out, "w")
	with open(file_in) as f:
		for line in f:
			line_list = line.strip().split()
			assert len(line_list) == 301

			f_out.write(line_list[0] + "\t" + str(ind) + "\n")
			ind += 1

	f_out.close()
	print ind

def read_word2vec_zip(word2vec_file):
    wordvec_map = {}
    num_words = 0
    dimension = 0
    zfile = zipfile.ZipFile(word2vec_file)
    for finfo in zfile.infolist():
        ifile = zfile.open(finfo)
        for line in ifile:
            line = line.strip()
            #print line
            entries = line.split(' ')
            if len(entries) == 2:
                continue
            word = entries[0].strip()
            vec = map(float, entries[1:])

            if word in wordvec_map:
                print ("Invalid word in embedding. Does not matter.")
                continue
            assert dimension == 0 or dimension == len(vec)

            wordvec_map[word] = np.array(vec)
            num_words += 1
            dimension = len(vec)

    return wordvec_map, num_words, dimension




def check_glove_coverage(glove_in, field_in):

	word2vec_map, _, _ = read_word2vec_zip(glove_in)

	word_vocab = {}
	with open(field_in) as f:
		for line in f:
			line_list = line.strip().split("\t")
			for each_word in line_list[0].split("_"):
				if each_word.strip() != "" and each_word not in word_vocab:
					word_vocab[each_word] = -1

	covered = 0
	for word in word_vocab:
		if word in word2vec_map:
			covered += 1


	print float(covered) / len(word_vocab)

def load_vocab(vocab_file):
	vocab = {}

	vocab['<_PAD>'] = 0
	vocab['<_START_TOKEN>'] = 1
	vocab['<_END_TOKEN>'] = 2
	vocab['<_UNK_TOKEN>'] = 3

	cnt = 4
	with open(vocab_file, "r") as v:
		for line in v:
			if len(line.strip().split()) > 1:
				word = line.strip().split()[0]
				ori_id = int(line.strip().split()[1])
				if word not in vocab:
					vocab[word] = (cnt + ori_id)

	return vocab


def check_in_vocab(check_vocab, word_to_check):
	'''
	check if a word in glove vocab
	'''

	vocab = load_vocab(check_vocab)

	if word_to_check in vocab:
		print "Yes"
	else:
		print "No"


def process_songs(file_in, file_out):
	'''
	extra process remove ""
	`` 365 nichi kazoku '' is a single release by the japanese boyband kanjani8 .
	'''
	f_out = open(file_out, "w")
	with open(file_in) as f:
		for line in f:
			summary = line.strip()
			if summary[0] == "`":
				summary = summary[3:]
				sum_list = summary.split("''")
				if len(sum_list) > 1:
					summary = sum_list[0].strip() + "''".join(sum_list[1:])

			f_out.write(summary + "\n")

	f_out.close()


def join_box(list_in):
	'''
	join original format values
	'''

	out_list = []
	current_name = ""
	current_value = ""
	# print "\n"
	# print list_in

	for each_item in list_in:
		field_name = each_item.split(":")[0]
		field_value = each_item.split(":")[1]

		if not field_name[-1].isdigit():
			if field_value != "<none>":
				out_list.append((field_name, field_value))
			continue

		field_name = "_".join(field_name.split("_")[:-1])

		if field_name != current_name:
			if current_name != "":
				cur_name_list = [tup[0] for tup in out_list]
				# print out_list
				# print field_name
				# assert field_name not in cur_name_list

				### remove none value
				if current_value.strip() != "<none>":
					out_list.append((current_name, current_value.strip()))
				current_name = ""
				current_value = ""

		current_name = field_name
		current_value += (field_value + " ")


	if current_value.strip() != "<none>":
		out_list.append((current_name, current_value.strip()))

	sorted_by_second = sorted(out_list, key=lambda tup: len(tup[1].split(" ")), reverse=True)

	return out_list, sorted_by_second


# def fuzzy_match(source, substring):

# 	res = find_near_matches(substring, source, max_deletions=3, max_insertions=3, max_substitutions=0)
# 	if len(res) == 0:
# 		return None

# 	result = res[0]

# 	fuzzy_res = source[result[0]:result[1]]
# 	if source[result[0] - 1] == " " and source[result[1]] == " ":

# 		### expand
# 		# forward
# 		before = source[:result[0]].strip().split(" ")[-1]
# 		if before in substring:
# 			fuzzy_res = before + " " + fuzzy_res
# 		after = source[result[1]:].strip().split(" ")[0]
# 		if after in substring:
# 			fuzzy_res = fuzzy_res + " " + after

# 		return fuzzy_res

# 	else:
# 		return None

def load_dem_map(file_in):
	'''
	recursively load nationality map
	'''
	dem_map = {}
	with open(file_in) as f:
		for line in f:
			line_list = line.strip().lower().split(",")
			if line_list[0] not in dem_map:
				dem_map[line_list[0]] = []
			if line_list[1] not in dem_map[line_list[0]]:
				dem_map[line_list[0]].append(line_list[1])

			if line_list[1] not in dem_map:
				dem_map[line_list[1]] = []
			if line_list[0] not in dem_map[line_list[1]]:
				dem_map[line_list[1]].append(line_list[0])

	final_res_map = {}
	for each_con in dem_map:
		res_con = []
		q = Queue.Queue()
		q.put(each_con)

		while not q.empty():
			con = q.get()
			if con in res_con:
				continue

			res_con.append(con)
			if con in dem_map:
				for each_sub in dem_map[con]:
					q.put(each_sub)

		final_res_map[each_con] = res_con

	return final_res_map


def fuzzy_match(source, substring, field_name):

	this_value = substring
	out_summary = source

	this_value_list_raw = this_value.split(" ")
	out_summary_list = out_summary.split(" ")
	# print this_value_list
	# print out_summary_list

	this_value_list = []
	for token in this_value_list_raw:
		if not(token in string.punctuation) \
			and token != "-lrb-" \
			and token != "-rrb-" \
			and token != "-lsb-" \
			and token != "-rsb-":
			this_value_list.append(token)

	if len(this_value_list) == 0:
		return out_summary

	num_consist = 0
	min_index = len(out_summary_list) + 1
	max_index = -1

	for token in this_value_list:
		if token in out_summary_list:
			num_consist += 1
			this_ind = out_summary_list.index(token)
			if this_ind < min_index:
				min_index = this_ind
			if this_ind > max_index:
				max_index = this_ind

	# print num_consist
	# print min_index
	# print max_index


	if float(num_consist) / len(this_value_list) > 0.4:
		if max_index - min_index <= 2 * len(this_value_list):
			### regard as match
			to_replace = " ".join(out_summary_list[min_index:max_index+1])
			if out_summary.startswith(to_replace):
				out_summary = out_summary.replace(to_replace + " ", "<" + field_name + "> ")
			else:
				out_summary = out_summary.replace(" " + to_replace + " ", " <" + field_name + "> ")

	return out_summary



def gen_mask(in_summary, in_box, out_summary, out_box, out_join):
	'''
	replace special token with unk
	'''

	### load nationality demonyms.csv
	dem_map = load_dem_map("/scratch/home/zhiyu/wiki2bio/other_data/demonyms.csv")


	with open(in_box) as f:
		lines_box = f.readlines()

	with open(in_summary) as f:
		lines_summary = f.readlines()

	out_s = open(out_summary, "w")
	out_b = open(out_box, "w")
	out_t = open(out_join, "w")

	for box, summary in zip (lines_box, lines_summary):

		box_list = box.strip().split("\t")
		box_out_list, box_field_list = join_box(box_list)

		out_summary = summary.strip()

		for (this_name, this_value) in box_field_list:


			if " " + this_value + " " in out_summary:

				out_summary = out_summary.replace(" " + this_value + " ", " <" + this_name + "> ")

			### name
			elif out_summary.startswith(this_value):
				out_summary = out_summary.replace(this_value, "<" + this_name + ">")

			### nationality
			elif this_value in dem_map:
				this_value_list = dem_map[this_value]
				for this_value in this_value_list:
					if " " + this_value + " " in out_summary:

						out_summary = out_summary.replace(" " + this_value + " ", " <" + this_name + "> ")


			else:

				## seperate nationality
				is_dem_match = 0
				this_value_list = this_value.split(" , ")
				if len(this_value_list) > 1:
					for each_con in this_value_list:
						if " " + each_con + " " in out_summary and each_con in dem_map:
							out_summary = out_summary.replace(" " + each_con + " ", " <" + this_name + "> ")
							is_dem_match = 1
							break
						if each_con in dem_map:
							this_con_list = dem_map[each_con]
							for this_con in this_con_list:
								if " " + this_con + " " in out_summary:
									out_summary = out_summary.replace(" " + this_con + " ", " <" + this_name + "> ")
									is_dem_match = 1
									break

				if is_dem_match:
					continue

				### fuzzy match 
				# match threshold? len percent? start - end index offset
				out_summary = fuzzy_match(out_summary, this_value, this_name)



		# print box_list
		# print box_field_list
		# print out_summary
		# print summary
		# print "\n"

		out_b.write("\t".join([each_box[0] + ":" + each_box[1] for each_box in box_out_list]) + "\n")
		out_s.write(out_summary + "\n")

		out_t.write("\t".join([each_box[0] + ":" + each_box[1] for each_box in box_out_list]) + "\n")
		out_t.write(summary.strip() + "\n")
		out_t.write(out_summary + "\n")
		out_t.write("\n")



	out_s.close()
	out_b.close()
	out_t.close()







if __name__=='__main__':

	### generate mask
	# in_summary = "/scratch/home/zhiyu/wiki2bio/original_data/test.summary"
	# in_box = "/scratch/home/zhiyu/wiki2bio/original_data/test.box"
	# out_summary = "/scratch/home/zhiyu/wiki2bio/emb_baseline_mask/original_data/test.summary"
	# out_box = "/scratch/home/zhiyu/wiki2bio/emb_baseline_mask/original_data/test.box"
	# out_test_join = "/scratch/home/zhiyu/wiki2bio/emb_baseline_mask/original_data/test.join"

	# gen_mask(in_summary, in_box, out_summary, out_box, out_test_join)

	# herbert <article_title> , jr. -lrb- born april 21 , 1945 in <birth_place> -rrb- is a former american football player .

	# out_summary = "hassan taftian -lrb- ; born 4 may 1993 in torbat-e heydarieh -rrb- is an iranian sprinter ."
	# this_value = "04 may 1993"
	# print fuzzy_match(source, substring, "replace")


	# in_summary = "/scratch/home/zhiyu/wiki2bio/original_data/test.summary"
	# in_box = "/scratch/home/zhiyu/wiki2bio/original_data/test.box"
	# out_file = "/scratch/home/zhiyu/wiki2bio/masked_summary.txt"
	# gen_mask(in_summary, in_box, out_file)

	# file_in = "/scratch/home/zhiyu/wiki2bio/crawled_data/songs.summary.bak"
	# file_out = "/scratch/home/zhiyu/wiki2bio/crawled_data/songs.summary"
	# process_songs(file_in, file_out)

	# ori_vocab = "/scratch/home/zhiyu/wiki2bio/original_data/field_vocab.txt"

	# check_in_vocab(ori_vocab, "published")

	# file_in = summary_ours_in
	# file_out = "/scratch/home/zhiyu/wiki2bio/cider/data/candidate-baseline.json"
	# gen_cider_input(file_in, file_out)

	# file_in = summary_gold_in
	# file_out = "/scratch/home/zhiyu/wiki2bio/cider/data/references.json"
	# gen_cider_input(file_in, file_out)


	# gen_compare(cider_in, test_table, summary_ours_in, summary_with_unk, summary_gold_in, file_out)

	# metrics_dict = compute_metrics(hypothesis=summary_ours_in, references=[summary_gold_in])

	# print metrics_dict


	#check_field(train_table, "succession")

	#merge_value_field_vocab("/scratch/home/zhiyu/wiki2bio/original_data/")


	data_path = "/scratch/home/zhiyu/wiki2bio/crawled_data/pointer/"

	# domain = "books"
	# in_box = data_path + domain + ".box"
	# in_summary = data_path + domain + ".summary"
	# word_vocab_file = data_path + domain + "_word_vocab.txt"
	# field_vocab_file = data_path + domain + "_field_vocab.txt"

	# # # pc_all_vocab = "/scratch/home/zhiyu/wiki2bio/crawled_data/personal_computers_word_vocab_all.txt"
	# # # final_vocab = "/scratch/home/zhiyu/wiki2bio/crawled_data/merged_vocab.txt"
	# # # final_field_vocab = "/scratch/home/zhiyu/wiki2bio/crawled_data/merged_field_vocab.txt"

	books_all_vocab = data_path + "books_word_vocab_all.txt"
	songs_all_vocab = data_path + "songs_word_vocab_all.txt"
	films_all_vocab = data_path + "films_word_vocab_all.txt"

	# # # books_field_vocab = "/scratch/home/zhiyu/wiki2bio/crawled_data/books_field_vocab.txt"
	# # # songs_field_vocab = "/scratch/home/zhiyu/wiki2bio/crawled_data/songs_field_vocab.txt"
	# # # films_field_vocab = "/scratch/home/zhiyu/wiki2bio/crawled_data/films_field_vocab.txt"

	# create_ori_vocab(in_box, in_summary, word_vocab_file, field_vocab_file, 1999)
	# merge_value_field_vocab(word_vocab_file, field_vocab_file, books_all_vocab)

	ori_vocab = data_path + "word_vocab_2000.txt"
	final_vocab = data_path + "human_books_songs_films_word_vocab_2000.txt"

	# # # ori_field_vocab = "/scratch/home/zhiyu/wiki2bio/crawled_data/field_vocab.txt"
	# # # final_field_vocab = "/scratch/home/zhiyu/wiki2bio/crawled_data/human_books_songs_films_field_vocab.txt"

	add_vocab(ori_vocab, books_all_vocab, final_vocab)
	add_vocab(final_vocab, songs_all_vocab, final_vocab)
	add_vocab(final_vocab, films_all_vocab, final_vocab)

	# add_vocab(ori_field_vocab, books_field_vocab, final_field_vocab)
	# add_vocab(final_field_vocab, songs_field_vocab, final_field_vocab)
	# add_vocab(final_field_vocab, films_field_vocab, final_field_vocab)


	# file_in = "/scratch/home/zhiyu/wiki2bio/other_data/glove.6B.300d.txt"
	# file_out = "/scratch/home/zhiyu/wiki2bio/emb_baseline/word_vocab.txt"
	# extract_glove_vocab(file_in, file_out)


	# file_in = "/scratch/home/zhiyu/wiki2bio/original_data/word_vocab.txt"
	# file_out = "/scratch/home/zhiyu/wiki2bio/crawled_data/pointer/word_vocab_2000.txt"

	# vocab = []
	# ind = 0
	# with open(file_in) as f:
	# 	for line in f:
	# 		line_list = line.strip().split()
	# 		if line_list[0].isdigit():
	# 			continue
	# 		vocab.append((line_list[0], line_list[1]))
	# 		ind += 1

	# 		if ind > 1999:
	# 			break


	# print len(vocab)
	# with open(file_out, "w") as f:
	# 	for word in vocab:
	# 		f.write(word[0] + "\t" + word[1] + "\n")


	# ori_field = "/scratch/home/zhiyu/wiki2bio/original_data/field_vocab.txt"
	# file_in = "/scratch/home/zhiyu/wiki2bio/crawled_data/word_vocab_tmp.txt"
	# merge_value_field_vocab(file_in, ori_field, ori_vocab)


	# glove_in = "/scratch/home/zhiyu/wiki2bio/other_data/glove.42B.300d.zip"
	# field_in = "/scratch/home/zhiyu/wiki2bio/crawled_data/books_field_vocab.txt"
	# check_glove_coverage(glove_in, field_in)


























